/**
 * Thin public report delivery shell for reports.codestrata.ai (Slice 17.16).
 *
 * Browser → /r/<opaque-id> → api.codestrata.ai/api/v1/reports/<id>
 * Never exposes S3. Bounded cache for revoke semantics.
 *
 * Landing "/" is served from public/ via Workers static assets
 * (run_worker_first keeps this Worker on /r/* only).
 */

export interface Env {
  UPSTREAM_API_BASE: string;
  ASSETS: Fetcher;
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
  return (env.UPSTREAM_API_BASE || "https://api.codestrata.ai").replace(/\/$/, "");
}

function opaqueIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/r\/([A-Za-z0-9_-]{32,48})$/);
  return match ? match[1] : null;
}

async function fetchReport(
  request: Request,
  env: Env,
  publicId: string,
): Promise<Response> {
  const base = upstreamBase(env);
  const incoming = new URL(request.url);
  const format = incoming.searchParams.get("format");
  const target = new URL(`${base}/api/v1/reports/${publicId}`);
  if (format === "json" || format === "html") {
    target.searchParams.set("format", format);
  }

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  headers.set("Accept", format === "json" ? "application/json" : "text/html");

  const upstream = await fetch(target.toString(), {
    method: "GET",
    headers,
    redirect: "manual",
  });

  const out = new Headers(upstream.headers);
  // Enforce bounded cache so revoke can take effect quickly.
  out.set("Cache-Control", "private, max-age=60, must-revalidate");
  out.set("X-Robots-Tag", "noindex");
  return new Response(upstream.body, {
    status: upstream.status,
    headers: out,
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Branding/static assets must never be intercepted as report routes.
    // When a missing asset falls through to this Worker, serve via ASSETS.
    const publicId = opaqueIdFromPath(url.pathname);
    if (!publicId) {
      if (env.ASSETS) {
        return env.ASSETS.fetch(request);
      }
      return new Response(JSON.stringify({ error: "not_found" }), {
        status: 404,
        headers: {
          "content-type": "application/json",
          "cache-control": "private, max-age=60, must-revalidate",
        },
      });
    }

    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response(JSON.stringify({ error: "method_not_allowed" }), {
        status: 405,
        headers: { "content-type": "application/json" },
      });
    }

    return fetchReport(request, env, publicId);
  },
};
