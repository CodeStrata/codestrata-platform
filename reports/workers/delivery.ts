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

function newFeedbackNonce(): string {
  const bytes = new Uint8Array(18);
  crypto.getRandomValues(bytes);
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function publishedFeedbackCsp(nonce: string): string {
  return (
    "default-src 'none'; " +
    "base-uri 'none'; " +
    "form-action 'none'; " +
    "frame-ancestors 'none'; " +
    "img-src data:; " +
    "font-src 'none'; " +
    "connect-src 'self'; " +
    "object-src 'none'; " +
    `script-src 'nonce-${nonce}'; ` +
    "style-src 'unsafe-inline'"
  );
}

function applyPublishedFeedbackCsp(html: string, nonce: string): string {
  const policy = publishedFeedbackCsp(nonce);
  const metaRe =
    /(<meta\s+http-equiv=["']Content-Security-Policy["']\s+content=)(?:"([^"]*)"|'([^']*)')(\s*\/?>)/i;
  if (metaRe.test(html)) {
    return html.replace(metaRe, (_full, prefix: string, dq: string, sq: string, suffix: string) => {
      const quote = dq !== undefined ? '"' : "'";
      return `${prefix}${quote}${policy}${quote}${suffix}`;
    });
  }
  const meta = `<meta http-equiv="Content-Security-Policy" content="${policy}">`;
  const headClose = html.toLowerCase().indexOf("</head>");
  if (headClose >= 0) {
    return html.slice(0, headClose) + meta + html.slice(headClose);
  }
  return meta + html;
}

function feedbackFooterHtml(publicId: string, nonce: string): string {
  const safe = publicId
    .replace(/\\/g, "\\\\")
    .replace(/'/g, "\\'")
    .replace(/</g, "\\u003c")
    .replace(/>/g, "\\u003e");
  const safeAttr = publicId
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
  return `
<footer id="cs-report-feedback" data-public-id="${safeAttr}" style="font-family:system-ui,sans-serif;padding:20px 16px;border-top:1px solid #d0d7de;margin-top:24px;background:#fafbfc;">
  <div id="cs-feedback-prompt">
    <p style="margin:0 0 10px;font-size:14px;">Was this report useful?</p>
    <button type="button" data-useful="yes" style="margin-right:8px;padding:6px 14px;cursor:pointer;">Yes</button>
    <button type="button" data-useful="no" style="padding:6px 14px;cursor:pointer;">No</button>
    <p id="cs-feedback-error" style="display:none;margin:10px 0 0;font-size:12px;color:#cf222e;"></p>
  </div>
  <p id="cs-feedback-thanks" style="display:none;margin:0;font-size:14px;">Thank you for your feedback.</p>
</footer>
<script nonce="${nonce}">
(function () {
  var root = document.getElementById("cs-report-feedback");
  if (!root) return;
  var publicId = root.getAttribute("data-public-id") || "${safe}";
  var prompt = document.getElementById("cs-feedback-prompt");
  var thanks = document.getElementById("cs-feedback-thanks");
  var err = document.getElementById("cs-feedback-error");
  var tokenKey = "cs_feedback_respondent";
  var voteKey = "cs_feedback_vote_" + publicId;
  var inflight = false;
  function buttons() {
    return root.querySelectorAll("button[data-useful]");
  }
  function setBusy(busy) {
    inflight = busy;
    buttons().forEach(function (b) { b.disabled = busy; });
  }
  function ensureToken() {
    try {
      var t = localStorage.getItem(tokenKey);
      if (t && t.length >= 16) return t;
      t = (window.crypto && crypto.randomUUID)
        ? crypto.randomUUID().replace(/-/g, "") + crypto.randomUUID().replace(/-/g, "").slice(0, 8)
        : ("cs" + String(Date.now()) + Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2));
      localStorage.setItem(tokenKey, t.slice(0, 64));
      return localStorage.getItem(tokenKey);
    } catch (e) { return null; }
  }
  function showThanks() {
    if (prompt) prompt.style.display = "none";
    if (thanks) thanks.style.display = "block";
    if (err) err.style.display = "none";
  }
  function showError(msg) {
    if (!err) return;
    err.textContent = msg || "We couldn't save your feedback. Please try again.";
    err.style.display = "block";
  }
  try {
    var prior = localStorage.getItem(voteKey);
    if (prior === "yes" || prior === "no") showThanks();
  } catch (e) {}
  root.addEventListener("click", function (ev) {
    var btn = ev.target && ev.target.closest ? ev.target.closest("button[data-useful]") : null;
    if (!btn || inflight) return;
    var useful = btn.getAttribute("data-useful");
    if (useful !== "yes" && useful !== "no") return;
    var token = ensureToken();
    if (!token) { showError("Feedback unavailable in this browser."); return; }
    setBusy(true);
    if (err) err.style.display = "none";
    fetch("/r/" + encodeURIComponent(publicId) + "/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({ schema_version: "1.0", useful: useful, respondent_token: token })
    }).then(function (res) {
      if (!res.ok) throw new Error("http_" + res.status);
      try { localStorage.setItem(voteKey, useful); } catch (e) {}
      showThanks();
    }).catch(function () {
      setBusy(false);
      showError("We couldn't save your feedback. Please try again.");
    });
  });
})();
</script>
`;
}

function extractFeedbackNonce(html: string): string | null {
  const match = html.match(
    /<footer\s+id=["']cs-report-feedback["'][\s\S]*?<script\s+nonce=["']([^"']+)["']/i,
  );
  return match ? match[1] : null;
}

function replaceFeedbackChrome(html: string, publicId: string, nonce: string): string {
  const footer = feedbackFooterHtml(publicId, nonce).trim();
  const replaced = html.replace(
    /<footer\s+id=["']cs-report-feedback["'][\s\S]*?<\/script>/i,
    footer,
  );
  if (replaced.includes('id="cs-report-feedback"')) {
    return applyPublishedFeedbackCsp(replaced, nonce);
  }
  const closeIdx = html.toLowerCase().lastIndexOf("</body>");
  const body =
    closeIdx >= 0 ? html.slice(0, closeIdx) + footer + html.slice(closeIdx) : html + footer;
  return applyPublishedFeedbackCsp(body, nonce);
}

function cspAllowsFeedback(html: string, nonce: string): boolean {
  const match = html.match(
    /<meta\s+http-equiv=["']Content-Security-Policy["']\s+content=(?:"([^"]*)"|'([^']*)')/i,
  );
  if (!match) return false;
  const policy = match[1] ?? match[2] ?? "";
  return (
    policy.includes(`script-src 'nonce-${nonce}'`) &&
    policy.includes("connect-src 'self'")
  );
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
  let body: string;
  if (html.includes('id="cs-report-feedback"')) {
    const existingNonce = extractFeedbackNonce(html);
    if (existingNonce && cspAllowsFeedback(html, existingNonce)) {
      body = html;
    } else if (existingNonce) {
      body = applyPublishedFeedbackCsp(html, existingNonce);
      if (!cspAllowsFeedback(body, existingNonce)) {
        body = replaceFeedbackChrome(html, publicId, existingNonce);
      }
    } else {
      body = replaceFeedbackChrome(html, publicId, newFeedbackNonce());
    }
  } else {
    const nonce = newFeedbackNonce();
    const footer = feedbackFooterHtml(publicId, nonce);
    const lower = html.toLowerCase();
    const closeIdx = lower.lastIndexOf("</body>");
    const assembled =
      closeIdx >= 0 ? html.slice(0, closeIdx) + footer + html.slice(closeIdx) : html + footer;
    body = applyPublishedFeedbackCsp(assembled, nonce);
  }
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

  // Oversized reports may 307 to a short-lived private GetObject URL.
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
