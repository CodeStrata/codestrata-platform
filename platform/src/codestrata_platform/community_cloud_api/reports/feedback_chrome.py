"""Published-report feedback chrome (CSP-compatible).

Local/offline Engine HTML keeps ``script-src 'none'`` / ``connect-src 'none'``.
Only published chrome rewrites CSP narrowly so Yes/No can POST same-origin.
"""

from __future__ import annotations

import re
import secrets
from html import escape

_CSP_META_RE = re.compile(
    r'(<meta\s+http-equiv=["\']Content-Security-Policy["\']\s+content=)'
    r'(?:"([^"]*)"|\'([^\']*)\')'
    r'(\s*/?>)',
    re.IGNORECASE,
)


def new_feedback_script_nonce() -> str:
    return secrets.token_urlsafe(18)


def published_feedback_csp(*, nonce: str) -> str:
    """Narrow published CSP: allow only this page's feedback script + same-origin POST."""

    return (
        "default-src 'none'; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "frame-ancestors 'none'; "
        "img-src data:; "
        "font-src 'none'; "
        f"connect-src 'self'; "
        "object-src 'none'; "
        f"script-src 'nonce-{nonce}'; "
        "style-src 'unsafe-inline'"
    )


def apply_published_feedback_csp(html: str, *, nonce: str) -> str:
    """Rewrite or insert CSP so the feedback nonce + connect-src 'self' are allowed."""

    policy = published_feedback_csp(nonce=nonce)

    def _replace(match: re.Match[str]) -> str:
        # Preserve the original quote style around content=.
        quoted = match.group(2)
        quote = '"' if quoted is not None else "'"
        value = quoted if quoted is not None else match.group(3)
        assert value is not None
        return f"{match.group(1)}{quote}{policy}{quote}{match.group(4)}"

    updated, count = _CSP_META_RE.subn(_replace, html, count=1)
    if count:
        return updated

    meta = f'<meta http-equiv="Content-Security-Policy" content="{policy}">'
    lower = html.lower()
    head_close = lower.find("</head>")
    if head_close >= 0:
        return html[:head_close] + meta + html[head_close:]
    return meta + html


def feedback_chrome_html(*, public_id: str, nonce: str | None = None) -> tuple[str, str]:
    """Return (html_fragment, nonce) for the voluntary Yes/No footer + handler."""

    script_nonce = nonce or new_feedback_script_nonce()
    safe_attr = escape(public_id, quote=True)
    pid_js = (
        public_id.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    html = f"""
<footer id="cs-report-feedback" data-public-id="{safe_attr}" style="font-family:system-ui,sans-serif;padding:20px 16px;border-top:1px solid #d0d7de;margin-top:24px;background:#fafbfc;">
  <div id="cs-feedback-prompt">
    <p style="margin:0 0 10px;font-size:14px;">Was this report useful?</p>
    <button type="button" data-useful="yes" style="margin-right:8px;padding:6px 14px;cursor:pointer;">Yes</button>
    <button type="button" data-useful="no" style="padding:6px 14px;cursor:pointer;">No</button>
    <p id="cs-feedback-error" style="display:none;margin:10px 0 0;font-size:12px;color:#cf222e;"></p>
  </div>
  <p id="cs-feedback-thanks" style="display:none;margin:0;font-size:14px;">Thank you for your feedback.</p>
</footer>
<script nonce="{script_nonce}">
(function () {{
  var root = document.getElementById("cs-report-feedback");
  if (!root) return;
  var publicId = root.getAttribute("data-public-id") || "{pid_js}";
  var prompt = document.getElementById("cs-feedback-prompt");
  var thanks = document.getElementById("cs-feedback-thanks");
  var err = document.getElementById("cs-feedback-error");
  var tokenKey = "cs_feedback_respondent";
  var voteKey = "cs_feedback_vote_" + publicId;
  var inflight = false;
  function buttons() {{
    return root.querySelectorAll("button[data-useful]");
  }}
  function setBusy(busy) {{
    inflight = busy;
    buttons().forEach(function (b) {{ b.disabled = busy; }});
  }}
  function ensureToken() {{
    try {{
      var t = localStorage.getItem(tokenKey);
      if (t && t.length >= 16) return t;
      t = (window.crypto && crypto.randomUUID)
        ? crypto.randomUUID().replace(/-/g, "") + crypto.randomUUID().replace(/-/g, "").slice(0, 8)
        : ("cs" + String(Date.now()) + Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2));
      localStorage.setItem(tokenKey, t.slice(0, 64));
      return localStorage.getItem(tokenKey);
    }} catch (e) {{ return null; }}
  }}
  function showThanks() {{
    if (prompt) prompt.style.display = "none";
    if (thanks) thanks.style.display = "block";
    if (err) err.style.display = "none";
  }}
  function showError(msg) {{
    if (!err) return;
    err.textContent = msg || "We couldn't save your feedback. Please try again.";
    err.style.display = "block";
  }}
  try {{
    var prior = localStorage.getItem(voteKey);
    if (prior === "yes" || prior === "no") showThanks();
  }} catch (e) {{}}
  root.addEventListener("click", function (ev) {{
    var btn = ev.target && ev.target.closest ? ev.target.closest("button[data-useful]") : null;
    if (!btn || inflight) return;
    var useful = btn.getAttribute("data-useful");
    if (useful !== "yes" && useful !== "no") return;
    var token = ensureToken();
    if (!token) {{ showError("Feedback unavailable in this browser."); return; }}
    setBusy(true);
    if (err) err.style.display = "none";
    fetch("/r/" + encodeURIComponent(publicId) + "/feedback", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json", "Accept": "application/json" }},
      body: JSON.stringify({{ schema_version: "1.0", useful: useful, respondent_token: token }})
    }}).then(function (res) {{
      if (!res.ok) throw new Error("http_" + res.status);
      try {{ localStorage.setItem(voteKey, useful); }} catch (e) {{}}
      showThanks();
    }}).catch(function () {{
      setBusy(false);
      showError("We couldn't save your feedback. Please try again.");
    }});
  }});
}})();
</script>
"""
    return html, script_nonce


__all__ = [
    "apply_published_feedback_csp",
    "feedback_chrome_html",
    "new_feedback_script_nonce",
    "published_feedback_csp",
]
