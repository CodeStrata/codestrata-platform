/**
 * Same-origin /api proxy → Community Cloud API (Slice 17.8).
 *
 * Forwards method, headers, and body. Preserves Set-Cookie for host-only
 * insights.codestrata.ai sessions. Does not introduce AWS SDK or secrets.
 */

export interface Env {
  ASSETS: Fetcher;
  UPSTREAM_API_BASE: string;
}

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

function upstreamBase(env: Env): string {
  return (env.UPSTREAM_API_BASE || "").replace(/\/$/, "");
}

async function proxyApi(request: Request, env: Env): Promise<Response> {
  const base = upstreamBase(env);
  if (!base) {
    return new Response(JSON.stringify({ error: "upstream_unconfigured" }), {
      status: 503,
      headers: { "content-type": "application/json" },
    });
  }

  const incoming = new URL(request.url);
  const target = new URL(incoming.pathname + incoming.search, `${base}/`);

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  // Preserve browser Origin for CSRF checks against insights.codestrata.ai.
  if (!headers.has("origin") && incoming.origin) {
    headers.set("origin", incoming.origin);
  }

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: "manual",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  const upstream = await fetch(target.toString(), init);
  const outHeaders = new Headers(upstream.headers);
  // Ensure browsers store host-only cookies on insights.codestrata.ai.
  const setCookies =
    typeof upstream.headers.getSetCookie === "function"
      ? upstream.headers.getSetCookie()
      : [];
  if (setCookies.length > 0) {
    outHeaders.delete("set-cookie");
    for (const cookie of setCookies) {
      // Strip any accidental Domain= so cookie stays host-only on the SPA host.
      const cleaned = cookie
        .split(";")
        .map((p) => p.trim())
        .filter((p) => !/^domain=/i.test(p))
        .join("; ");
      outHeaders.append("set-cookie", cleaned);
    }
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: outHeaders,
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/api" || url.pathname.startsWith("/api/")) {
      return proxyApi(request, env);
    }
    return env.ASSETS.fetch(request);
  },
};
