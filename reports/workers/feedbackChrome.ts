/**
 * Published-report feedback chrome helpers (CSP + footer).
 * Shared by the Cloudflare delivery Worker and deterministic unit tests.
 */

export function newFeedbackNonce(): string {
  const bytes = new Uint8Array(18);
  crypto.getRandomValues(bytes);
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

export function publishedFeedbackCsp(nonce: string): string {
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

export function applyPublishedFeedbackCsp(html: string, nonce: string): string {
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

export function feedbackFooterHtml(publicId: string, nonce: string): string {
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

export function extractFeedbackNonce(html: string): string | null {
  const match = html.match(
    /<footer\s+id=["']cs-report-feedback["'][\s\S]*?<script\s+nonce=["']([^"']+)["']/i,
  );
  return match ? match[1] : null;
}

export function replaceFeedbackChrome(html: string, publicId: string, nonce: string): string {
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

export function cspAllowsFeedback(html: string, nonce: string): boolean {
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

/**
 * Pure HTML transform used by the Worker when injecting/fixing feedback chrome.
 * Tests pass an explicit nonce for determinism.
 */
export function transformHtmlForPublicFeedback(
  html: string,
  publicId: string,
  nonce: string = newFeedbackNonce(),
): string {
  if (html.includes('id="cs-report-feedback"')) {
    const existingNonce = extractFeedbackNonce(html);
    if (existingNonce && cspAllowsFeedback(html, existingNonce)) {
      return html;
    }
    if (existingNonce) {
      const rewritten = applyPublishedFeedbackCsp(html, existingNonce);
      if (!cspAllowsFeedback(rewritten, existingNonce)) {
        return replaceFeedbackChrome(html, publicId, existingNonce);
      }
      return rewritten;
    }
    return replaceFeedbackChrome(html, publicId, nonce);
  }
  const footer = feedbackFooterHtml(publicId, nonce);
  const lower = html.toLowerCase();
  const closeIdx = lower.lastIndexOf("</body>");
  const assembled =
    closeIdx >= 0 ? html.slice(0, closeIdx) + footer + html.slice(closeIdx) : html + footer;
  return applyPublishedFeedbackCsp(assembled, nonce);
}
