/**
 * Slice 13.7 HTML report-opening unit tests.
 */

import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { describe, it } from "node:test";

import {
  ENGINE_HTML_REPORT_BASENAME,
  REPORT_OPENING_POLICY_ID,
  REPORT_OPENING_POLICY_VERSION,
  createReportOpeningPolicy,
  isPathInsideRoot,
  locateHtmlReport,
  openValidatedHtmlReport,
  reportDiagnosticsContainForbiddenKeys,
  reportOpeningDiagnosticsToStableDict,
  reportOpeningPolicyToStableDict,
  reportOpeningResultToStableDict,
  resolveApprovedOutputRoot,
  validateHtmlReportFile,
  diagnosticsFromReportResult,
} from "../reportOpening";
import { EXCLUDED_TELEMETRY_COMMANDS } from "../telemetry/promptPolicy";

function tempRepo(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), "cs-report-"));
}

function writeHtmlReport(repo: string, outputRel = "reports"): string {
  const run = path.join(repo, outputRel, "demo-repo", "20260101-120000");
  fs.mkdirSync(run, { recursive: true });
  const html = path.join(run, ENGINE_HTML_REPORT_BASENAME);
  fs.writeFileSync(html, "<html><body>ok</body></html>", "utf8");
  return html;
}

describe("report opening policy", () => {
  it("serializes as prompt-driven local HTML open", () => {
    const a = reportOpeningPolicyToStableDict(createReportOpeningPolicy());
    const b = reportOpeningPolicyToStableDict(createReportOpeningPolicy());
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.policy_id, REPORT_OPENING_POLICY_ID);
    assert.equal(a.policy_version, REPORT_OPENING_POLICY_VERSION);
    assert.equal(a.automatic_open_after_success, false);
    assert.equal(a.filesystem_crawl_allowed, false);
    assert.equal(a.telemetry_allowed, false);
    assert.equal(a.analytics_allowed, false);
    assert.equal(JSON.stringify(a).includes("/Users/"), false);
  });
});

describe("path containment", () => {
  it("rejects absolute output escape and traversal", () => {
    const repo = tempRepo();
    try {
      const ok = resolveApprovedOutputRoot(repo, "reports");
      assert.equal(ok.contained, true);
      const escaped = resolveApprovedOutputRoot(repo, "/tmp/outside");
      assert.equal(escaped.contained, false);
      assert.equal(
        isPathInsideRoot(repo, path.join(repo, "reports", "x")),
        true
      );
      assert.equal(
        isPathInsideRoot(repo, path.join(repo, "..", "escape.html")),
        false
      );
    } finally {
      fs.rmSync(repo, { recursive: true, force: true });
    }
  });

  it("validates report.html only inside output root", () => {
    const repo = tempRepo();
    try {
      const html = writeHtmlReport(repo);
      const good = validateHtmlReportFile({
        workspaceRoot: repo,
        outputDirectory: "reports",
        candidatePath: html,
      });
      assert.equal(good.ok, true);

      const outside = path.join(repo, "evil.html");
      fs.writeFileSync(outside, "<html></html>", "utf8");
      const bad = validateHtmlReportFile({
        workspaceRoot: repo,
        outputDirectory: "reports",
        candidatePath: outside,
      });
      assert.equal(bad.ok, false);

      const dirAsHtml = path.join(repo, "reports", "demo-repo", "report.html");
      fs.mkdirSync(path.dirname(dirAsHtml), { recursive: true });
      // ensure conflict: create directory named report.html under a run
      const run = path.join(repo, "reports", "demo-repo", "dirrun");
      fs.mkdirSync(run, { recursive: true });
      const htmlDir = path.join(run, "report.html");
      fs.mkdirSync(htmlDir);
      const dirCheck = validateHtmlReportFile({
        workspaceRoot: repo,
        outputDirectory: "reports",
        candidatePath: htmlDir,
      });
      assert.equal(dirCheck.ok, false);
    } finally {
      fs.rmSync(repo, { recursive: true, force: true });
    }
  });
});

describe("locate and open", () => {
  it("locates bounded HTML report and opens via adapter", async () => {
    const repo = tempRepo();
    try {
      const html = writeHtmlReport(repo);
      const located = locateHtmlReport({
        workspaceRoot: repo,
        outputDirectory: "reports",
      });
      assert.equal(located.status, "available");
      assert.equal(
        fs.realpathSync(located.htmlPath!),
        fs.realpathSync(html)
      );

      let openedPath = "";
      const result = await openValidatedHtmlReport({
        workspaceRoot: repo,
        outputDirectory: "reports",
        htmlPath: located.htmlPath,
        open: {
          async openLocalFile(p) {
            openedPath = p;
            return true;
          },
        },
      });
      assert.equal(result.status, "opened");
      assert.equal(result.primary_result_preserved, true);
      assert.equal(fs.realpathSync(openedPath), fs.realpathSync(html));
      assert.equal(result.open_succeeded, true);
    } finally {
      fs.rmSync(repo, { recursive: true, force: true });
    }
  });

  it("isolates open failure and preserves primary", async () => {
    const repo = tempRepo();
    try {
      const html = writeHtmlReport(repo);
      const result = await openValidatedHtmlReport({
        workspaceRoot: repo,
        outputDirectory: "reports",
        htmlPath: html,
        open: {
          async openLocalFile() {
            return false;
          },
        },
      });
      assert.equal(result.status, "open_failed");
      assert.equal(result.primary_result_preserved, true);
    } finally {
      fs.rmSync(repo, { recursive: true, force: true });
    }
  });

  it("keeps diagnostics privacy-safe", () => {
    const result = diagnosticsFromReportResult(
      {
        status: "opened",
        report_expected: true,
        report_available: true,
        open_attempted: true,
        open_succeeded: true,
        user_action_required: false,
        primary_result_preserved: true,
        recovery_category: "none",
        limitations: [],
      },
      "open_report",
      "success"
    );
    const blob = reportOpeningDiagnosticsToStableDict(result);
    assert.deepEqual(reportDiagnosticsContainForbiddenKeys(blob), []);
    assert.equal(
      JSON.stringify(reportOpeningResultToStableDict({
        status: "opened",
        report_expected: true,
        report_available: true,
        open_attempted: true,
        open_succeeded: true,
        user_action_required: false,
        primary_result_preserved: true,
        recovery_category: "none",
        limitations: [],
      })).includes("file:"),
      false
    );
  });
});

describe("telemetry boundary for report open", () => {
  it("excludes codestrata.openHtmlReport from telemetry eligibility", () => {
    assert.ok(
      (EXCLUDED_TELEMETRY_COMMANDS as readonly string[]).includes(
        "codestrata.openHtmlReport"
      )
    );
  });
});
