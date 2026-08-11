/**
 * Unit tests for report publish helpers (Slice 17.21).
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  artifactsRootFromOutputDirectory,
  buildReportPublishArgs,
  isLocalOrPrivateRepositoryId,
  parsePublicReportUrl,
  publishEnvForReportPublish,
  repositoryIdFromHtmlPath,
} from "../reportPublishing/orchestration";
import {
  REPORT_PUBLISH_COMMAND_ID,
  REPORT_PUBLISH_POLICY,
} from "../reportPublishing/policy";

describe("reportPublishing", () => {
  it("exposes stable command id", () => {
    assert.equal(REPORT_PUBLISH_COMMAND_ID, "codestrata.publishCurrentReport");
  });

  it("derives repository id from current assessment.html path", () => {
    assert.equal(
      repositoryIdFromHtmlPath(
        "/tmp/ws/.codestrata-artifacts/assessments/github-pallets-flask/current/assessment.html"
      ),
      "github-pallets-flask"
    );
    assert.equal(
      repositoryIdFromHtmlPath(
        "/tmp/ws/.codestrata-artifacts/assessments/local-flask/current/assessment.html"
      ),
      "local-flask"
    );
    assert.equal(repositoryIdFromHtmlPath("/tmp/nope.html"), undefined);
  });

  it("detects local repository ids", () => {
    assert.equal(isLocalOrPrivateRepositoryId("local-flask"), true);
    assert.equal(isLocalOrPrivateRepositoryId("github-pallets-flask"), false);
  });

  it("maps output directory to artifacts root", () => {
    assert.equal(
      artifactsRootFromOutputDirectory(".codestrata-artifacts/assessments"),
      ".codestrata-artifacts"
    );
  });

  it("builds publish args with explicit confirms", () => {
    const args = buildReportPublishArgs({
      repositoryId: "local-flask",
      artifactsRoot: ".codestrata-artifacts",
      acknowledgePrivate: true,
    });
    assert.deepEqual(args, [
      "report",
      "publish",
      "--type",
      "assessment",
      "--repository-id",
      "local-flask",
      "--artifacts-root",
      ".codestrata-artifacts",
      "--confirm-public-publish",
      "--acknowledge-private-repository",
    ]);
  });

  it("parses branded public URL and ignores non-matching hosts", () => {
    const url = parsePublicReportUrl(
      "Report published.\nPublic report: https://reports.codestrata.ai/r/abc123XYZ\n"
    );
    assert.equal(url, "https://reports.codestrata.ai/r/abc123XYZ");
    assert.equal(
      parsePublicReportUrl("https://bucket.s3.amazonaws.com/secret"),
      undefined
    );
  });

  it("does not require telemetry opt-in env for publish", () => {
    assert.equal(REPORT_PUBLISH_POLICY.requires_telemetry_opt_in_env, false);
    const env = publishEnvForReportPublish({
      CODESTRATA_TELEMETRY_OPT_IN: "true",
      PATH: "/usr/bin",
    });
    assert.equal(env.CODESTRATA_TELEMETRY_OPT_IN, undefined);
    assert.equal(env.PATH, "/usr/bin");
  });
});
