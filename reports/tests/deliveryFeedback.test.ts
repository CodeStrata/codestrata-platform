/**
 * REPORTS-WORKER-01…06 — delivery transformation / CSP / feedback wiring.
 */
import { describe, expect, it } from "vitest";
import {
  publishedFeedbackCsp,
  transformHtmlForPublicFeedback,
} from "../workers/feedbackChrome";

const PUBLIC_ID = "A".repeat(32);
const NONCE = "test-nonce-abcdef012345";

const ENGINE_OFFLINE_CSP =
  "default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; " +
  "img-src data:; font-src 'none'; connect-src 'none'; object-src 'none'; " +
  "script-src 'none'; style-src 'unsafe-inline'";

function engineLikeHtml(): string {
  return `<!DOCTYPE html><html><head>
<meta http-equiv="Content-Security-Policy" content="${ENGINE_OFFLINE_CSP}">
<link rel="icon" type="image/png" href="data:image/png;base64,AAAA">
<title>report</title>
</head><body><p>report body</p></body></html>`;
}

describe("Reports Worker delivery feedback chrome", () => {
  it("REPORTS-WORKER-01: Published HTML contains feedback chrome", () => {
    const out = transformHtmlForPublicFeedback(engineLikeHtml(), PUBLIC_ID, NONCE);
    expect(out).toContain('id="cs-report-feedback"');
    expect(out).toContain("Was this report useful?");
    expect(out).toContain('data-useful="yes"');
    expect(out).toContain('data-useful="no"');
  });

  it("REPORTS-WORKER-02: Published CSP allows nonce script only", () => {
    const out = transformHtmlForPublicFeedback(engineLikeHtml(), PUBLIC_ID, NONCE);
    expect(out).toContain(`script-src 'nonce-${NONCE}'`);
    expect(out).not.toContain("script-src 'none'");
    expect(out).not.toContain("script-src 'unsafe-inline'");
    expect(out).toContain(`<script nonce="${NONCE}">`);
  });

  it("REPORTS-WORKER-03: Published CSP uses connect-src 'self'", () => {
    const out = transformHtmlForPublicFeedback(engineLikeHtml(), PUBLIC_ID, NONCE);
    expect(out).toContain("connect-src 'self'");
    expect(out).not.toContain("connect-src 'none'");
    expect(publishedFeedbackCsp(NONCE)).toContain("connect-src 'self'");
  });

  it("REPORTS-WORKER-04: No unsafe-inline script / connect-src * / eval", () => {
    const out = transformHtmlForPublicFeedback(engineLikeHtml(), PUBLIC_ID, NONCE);
    const cspMatch = out.match(
      /Content-Security-Policy["']\s+content=(?:"([^"]*)"|'([^']*)')/i,
    );
    expect(cspMatch).toBeTruthy();
    const policy = cspMatch![1] ?? cspMatch![2] ?? "";
    expect(policy).not.toContain("connect-src *");
    expect(policy).not.toMatch(/script-src[^;]*'unsafe-inline'/);
    expect(policy.toLowerCase()).not.toContain("eval");
    expect(out.toLowerCase()).not.toContain("javascript:void");
    // style-src 'unsafe-inline' remains (Engine offline convention) — not script.
    expect(policy).toContain("style-src 'unsafe-inline'");
  });

  it("REPORTS-WORKER-05: Existing favicon survives delivery transformation", () => {
    const out = transformHtmlForPublicFeedback(engineLikeHtml(), PUBLIC_ID, NONCE);
    expect(out).toContain('rel="icon"');
    expect(out).toContain("data:image/png;base64,AAAA");
  });

  it("REPORTS-WORKER-06: Feedback endpoint path remains same-origin /r/<id>/feedback", () => {
    const out = transformHtmlForPublicFeedback(engineLikeHtml(), PUBLIC_ID, NONCE);
    expect(out).toContain(`fetch("/r/" + encodeURIComponent(publicId) + "/feedback"`);
    expect(out).not.toContain("api.codestrata.ai/api/v1/reports");
    expect(out).not.toContain("https://");
  });
});
