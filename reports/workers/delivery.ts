/**
 * Thin public report delivery shell for reports.codestrata.ai (Slice 17.16 / 19.4 / 20.13B).
 *
 * Browser → /r/<opaque-id> → api.codestrata.ai/api/v1/reports/<id>
 * Browser → /r/<opaque-id>/feedback → api.codestrata.ai/api/v1/reports/<id>/feedback
 * Never exposes S3. Bounded cache for revoke semantics.
 *
 * Oversized reports may be served from a Worker-followed presigned GET without
 * API chrome; this Worker injects the voluntary feedback footer for HTML.
 *
 * Engine offline CSP uses script-src/connect-src 'none'. Published delivery
 * rewrites CSP narrowly (nonce + connect-src 'self') so Yes/No can work.
 */

import { transformHtmlForPublicFeedback } from "./feedbackChrome";

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

function feedbackIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/r\/([A-Za-z0-9_-]{32,48})\/feedback$/);
  return match ? match[1] : null;
}

async function ensureFeedbackChrome(
  response: Response,
  publicId: string,
): Promise<Response> {
  const contentType = (response.headers.get("content-type") || "").toLowerCase();
  if (!contentType.includes("text/html")) {
    return response;
  }
  const html = await response.text();
  const body = transformHtmlForPublicFeedback(html, publicId);
  const out = new Headers(response.headers);
  out.set("Content-Type", "text/html; charset=utf-8");
  out.set("Cache-Control", "private, max-age=60, must-revalidate");
  out.set("X-Robots-Tag", "noindex");
  out.delete("content-length");
  return new Response(body, { status: response.status, headers: out });
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

  // Oversized reports may be served from a Worker-followed private GetObject URL.
  // Follow server-side so the browser stays on reports.codestrata.ai/r/<id>.
  if (upstream.status === 307 || upstream.status === 302) {
    const location = upstream.headers.get("location");
    if (location) {
      const artifact = await fetch(location, {
        method: "GET",
        redirect: "follow",
      });
      const out = new Headers();
      out.set(
        "Content-Type",
        artifact.headers.get("content-type") || "text/html; charset=utf-8",
      );
      out.set("Cache-Control", "private, max-age=60, must-revalidate");
      out.set("X-Robots-Tag", "noindex");
      out.set("X-CodeStrata-Report-Delivery", "worker_followed_presign");
      // Forward API identity headers from the 307 response (S3 object has none).
      const publicIdHeader = upstream.headers.get("X-CodeStrata-Public-Id");
      if (publicIdHeader) {
        out.set("X-CodeStrata-Public-Id", publicIdHeader);
      }
      const reportTypeHeader = upstream.headers.get("X-CodeStrata-Report-Type");
      if (reportTypeHeader) {
        out.set("X-CodeStrata-Report-Type", reportTypeHeader);
      }
      const wrapped = new Response(artifact.body, {
        status: artifact.status,
        headers: out,
      });
      if (format === "json") {
        return wrapped;
      }
      return ensureFeedbackChrome(wrapped, publicId);
    }
  }

  const out = new Headers(upstream.headers);
  out.set("Cache-Control", "private, max-age=60, must-revalidate");
  out.set("X-Robots-Tag", "noindex");
  const proxied = new Response(upstream.body, {
    status: upstream.status,
    headers: out,
  });
  if (format === "json" || request.method === "HEAD") {
    return proxied;
  }
  return ensureFeedbackChrome(proxied, publicId);
}

async function proxyFeedback(
  request: Request,
  env: Env,
  publicId: string,
): Promise<Response> {
  const base = upstreamBase(env);
  const target = `${base}/api/v1/reports/${publicId}/feedback`;
  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  if (!headers.has("content-type")) {
    headers.set("content-type", "application/json");
  }
  const body = await request.arrayBuffer();
  const upstream = await fetch(target, {
    method: "POST",
    headers,
    body,
  });
  const out = new Headers(upstream.headers);
  out.set("Cache-Control", "no-store");
  return new Response(upstream.body, {
    status: upstream.status,
    headers: out,
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    const feedbackId = feedbackIdFromPath(url.pathname);
    if (feedbackId) {
      if (request.method === "OPTIONS") {
        return new Response(null, {
          status: 204,
          headers: {
            "Access-Control-Allow-Origin": url.origin,
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Access-Control-Allow-Headers": "Accept,Content-Type",
            "Cache-Control": "no-store",
          },
        });
      }
      if (request.method !== "POST") {
        return new Response(JSON.stringify({ error: "method_not_allowed" }), {
          status: 405,
          headers: { "content-type": "application/json" },
        });
      }
      return proxyFeedback(request, env, feedbackId);
    }

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
