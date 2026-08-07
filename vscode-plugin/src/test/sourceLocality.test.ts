/**
 * Slice 13.10 source-locality unit tests.
 */

import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as path from "node:path";
import { describe, it } from "node:test";

import {
  APPROVED_ENGINE_ARTIFACT_BASENAMES,
  FORBIDDEN_OVERCLAIMS,
  SOURCE_LOCALITY_CLAIMS,
  SOURCE_LOCALITY_POLICY_ID,
  SOURCE_LOCALITY_POLICY_VERSION,
  claimsToStableDict,
  createSourceLocalityDiagnostics,
  createSourceLocalityPolicy,
  createSourceLocalityResult,
  expectedCategoryForOperation,
  localityDiagnosticsContainForbiddenKeys,
  sourceLocalityDiagnosticsToStableDict,
  sourceLocalityPolicyToStableDict,
  sourceLocalityResultToStableDict,
} from "../sourceLocality";

const SRC_ROOT = path.resolve(__dirname, "../../src");

function collectTsFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "test" || entry.name === "node_modules") {
      continue;
    }
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...collectTsFiles(full));
    } else if (entry.name.endsWith(".ts")) {
      out.push(full);
    }
  }
  return out;
}

describe("source locality policy", () => {
  it("serializes deterministically with upload forbidden", () => {
    const a = sourceLocalityPolicyToStableDict(createSourceLocalityPolicy());
    const b = sourceLocalityPolicyToStableDict(createSourceLocalityPolicy());
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.policy_id, SOURCE_LOCALITY_POLICY_ID);
    assert.equal(a.policy_version, SOURCE_LOCALITY_POLICY_VERSION);
    assert.equal(a.extension_source_upload_allowed, false);
    assert.equal(a.extension_cloud_api_access_allowed, false);
    assert.equal(a.extension_ai_provider_calls_allowed, false);
    assert.equal(a.ai_assessment_engine_provider_flow_possible, true);
    assert.equal(a.git_mutation_allowed, false);
  });
});

describe("operation categories", () => {
  it("maps AI assessment to engine provider boundary", () => {
    assert.equal(
      expectedCategoryForOperation("run_assessment"),
      "local_only"
    );
    assert.equal(
      expectedCategoryForOperation("run_assessment_with_ai"),
      "local_with_engine_ai_provider_boundary"
    );
    assert.equal(
      expectedCategoryForOperation("open_documentation"),
      "local_navigation_only"
    );
    const r = sourceLocalityResultToStableDict(
      createSourceLocalityResult({
        operation: "run_assessment_with_ai",
        category: "local_with_engine_ai_provider_boundary",
        source_read_category: "none",
        source_write_category: "engine_owned_via_cli",
        extension_network_category: "none",
        engine_network_category: "configured_ai_provider_possible",
        telemetry_category: "unavailable_or_privacy_projected",
        analytics_category: "unavailable_or_privacy_projected",
        generated_artifact_category: "local_report_artifact",
      })
    );
    assert.equal(r.identity_used, false);
    assert.equal(r.credential_used, false);
  });

  it("lists approved Engine artifact basenames", () => {
    assert.ok(APPROVED_ENGINE_ARTIFACT_BASENAMES.includes("report.html"));
    assert.ok(APPROVED_ENGINE_ARTIFACT_BASENAMES.includes("codestrata.toml"));
  });
});

describe("claims", () => {
  it("includes precise AI wording and forbidden overclaims", () => {
    assert.ok(
      SOURCE_LOCALITY_CLAIMS.ai_provider_engine_owned.includes(
        "configured AI provider"
      )
    );
    assert.ok(FORBIDDEN_OVERCLAIMS.includes("never leaves your machine"));
    const d = claimsToStableDict();
    assert.equal(JSON.stringify(d).includes("/Users/"), false);
  });
});

describe("diagnostics privacy", () => {
  it("omits forbidden keys", () => {
    const d = sourceLocalityDiagnosticsToStableDict(
      createSourceLocalityDiagnostics({
        operation: "run_assessment",
        engineAiProviderBoundary: "not_applicable",
        limitations: createSourceLocalityPolicy().limitations,
      })
    );
    assert.equal(localityDiagnosticsContainForbiddenKeys(d), false);
    assert.equal(d.extension_source_upload, false);
    assert.equal(d.cloud_client_used, false);
  });
});

describe("static production boundary", () => {
  it("production src has no network/SDK imports or writeFile", () => {
    const files = collectTsFiles(SRC_ROOT);
    assert.ok(files.length > 20);
    const forbiddenImportPatterns = [
      'from "axios"',
      "from 'axios'",
      'from "openai"',
      'from "@aws-sdk',
      'from "aws-sdk"',
      'from "codestrata_platform"',
      "from 'codestrata_platform'",
      "writeFileSync(",
      "writeFile(",
      "mkdirSync(",
      "git add",
      "git commit",
      "git push",
    ];
    for (const file of files) {
      if (file.includes(`${path.sep}test${path.sep}`)) {
        continue;
      }
      const text = fs.readFileSync(file, "utf8");
      assert.equal(
        text.includes("vscode.env.machineId"),
        false,
        `${file} reads machineId`
      );
      for (const needle of forbiddenImportPatterns) {
        assert.equal(
          text.includes(needle),
          false,
          `${file} contains ${needle}`
        );
      }
    }
  });
});
