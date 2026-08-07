/**
 * Slice 13.4 repository initialization unit tests.
 */

import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { describe, it } from "node:test";

import { buildInitArgs } from "../engine/cliContract";
import {
  assertInitArgsForbidForce,
  classifyConfigContents,
  createRepoInitResult,
  createRepositoryInitializationPolicy,
  detectRepositoryInitState,
  diagnosticsFromResult,
  planRepositoryInitialization,
  REPO_INIT_POLICY_ID,
  REPO_INIT_POLICY_VERSION,
  repoInitDiagnosticsContainForbiddenKeys,
  repositoryInitializationDiagnosticsToStableDict,
  repositoryInitializationPolicyToStableDict,
  repositoryInitializationResultToStableDict,
  resultAfterEngineInit,
  resultForPlanWithoutCli,
  userMessageForInitResult,
} from "../repositoryInitialization";
import { canTransition } from "../communityWorkflow";
import { EXCLUDED_TELEMETRY_COMMANDS } from "../telemetry/promptPolicy";
import { DEFAULT_SETTINGS } from "../config/settings";

function tempDir(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), "cs-repo-init-"));
}

describe("repository initialization policy", () => {
  it("serializes deterministically without paths or timestamps", () => {
    const a = repositoryInitializationPolicyToStableDict(
      createRepositoryInitializationPolicy()
    );
    const b = repositoryInitializationPolicyToStableDict(
      createRepositoryInitializationPolicy()
    );
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.policy_id, REPO_INIT_POLICY_ID);
    assert.equal(a.policy_version, REPO_INIT_POLICY_VERSION);
    assert.equal(a.engine_cli_authoritative, true);
    assert.equal(a.product_cli_invocation_count, 1);
    assert.equal(a.already_initialized_skips_cli, true);
    assert.equal(a.automatic_overwrite_allowed, false);
    assert.equal(a.assessment_allowed, false);
    assert.equal(a.telemetry_consent_allowed, false);
    assert.equal(a.analytics_allowed, false);
    assert.equal(a.ai_execution_allowed, false);
    assert.equal(a.report_open_allowed, false);
    const text = JSON.stringify(a);
    assert.equal(text.includes("/Users/"), false);
    assert.equal(text.includes("timestamp"), false);
  });
});

describe("initialization state detection", () => {
  it("classifies missing, empty, invalid, and valid configs", () => {
    const root = tempDir();
    try {
      assert.equal(
        detectRepositoryInitState({ workspaceRoot: root }).state,
        "not_initialized"
      );

      const cfg = path.join(root, "codestrata.toml");
      fs.writeFileSync(cfg, "", "utf8");
      assert.equal(
        detectRepositoryInitState({ workspaceRoot: root }).state,
        "partial_initialization"
      );

      fs.writeFileSync(cfg, "profile = \"community\"\n", "utf8");
      assert.equal(
        detectRepositoryInitState({ workspaceRoot: root }).state,
        "invalid_configuration"
      );

      fs.writeFileSync(
        cfg,
        "[repository]\npath = \".\"\nprofile = \"community\"\n",
        "utf8"
      );
      assert.equal(
        detectRepositoryInitState({ workspaceRoot: root }).state,
        "initialized"
      );

      assert.equal(classifyConfigContents(""), "partial_initialization");
      assert.equal(
        classifyConfigContents("[repository]\n"),
        "initialized"
      );
    } finally {
      fs.rmSync(root, { recursive: true, force: true });
    }
  });
});

describe("initialization plan and results", () => {
  it("skips CLI when already initialized (Approach A)", () => {
    const plan = planRepositoryInitialization("initialized");
    assert.equal(plan.action, "skip_already_initialized");
    const result = resultForPlanWithoutCli(plan as Exclude<typeof plan, { action: "invoke_engine_init" }>);
    assert.equal(result.status, "already_initialized");
    assert.equal(result.engine_invocation_count, 0);
    assert.equal(result.existing_configuration_preserved, true);
    assert.equal(result.assessment_invoked, false);
    assert.equal(result.telemetry_invoked, false);
    assert.equal(result.analytics_invoked, false);
    assert.equal(result.report_opened, false);
  });

  it("preserves invalid/partial config without CLI", () => {
    const invalid = resultForPlanWithoutCli(
      planRepositoryInitialization("invalid_configuration") as Exclude<
        ReturnType<typeof planRepositoryInitialization>,
        { action: "invoke_engine_init" }
      >
    );
    assert.equal(invalid.status, "invalid_existing_configuration");
    assert.equal(invalid.engine_invocation_count, 0);
    assert.equal(invalid.recovery_category, "inspect_existing_configuration");

    const partial = resultForPlanWithoutCli(
      planRepositoryInitialization("partial_initialization") as Exclude<
        ReturnType<typeof planRepositoryInitialization>,
        { action: "invoke_engine_init" }
      >
    );
    assert.equal(partial.status, "partial_existing_configuration");
  });

  it("verifies post-init and distinguishes cancel/fail/success", () => {
    assert.equal(
      resultAfterEngineInit({
        priorState: "not_initialized",
        cli: { exitCode: 0, cancelled: false },
        finalState: "initialized",
      }).status,
      "initialized"
    );
    assert.equal(
      resultAfterEngineInit({
        priorState: "not_initialized",
        cli: { exitCode: 0, cancelled: false },
        finalState: "not_initialized",
      }).status,
      "verification_failed"
    );
    assert.equal(
      resultAfterEngineInit({
        priorState: "not_initialized",
        cli: { exitCode: 1, cancelled: false },
        finalState: "not_initialized",
      }).status,
      "failed"
    );
    assert.equal(
      resultAfterEngineInit({
        priorState: "not_initialized",
        cli: { exitCode: 0, cancelled: true },
        finalState: "not_initialized",
      }).status,
      "cancelled"
    );
  });

  it("keeps diagnostics privacy-safe and deterministic", () => {
    const result = createRepoInitResult({
      status: "initialized",
      prior_state: "not_initialized",
      final_state: "initialized",
      engine_invocation_count: 1,
      config_created: true,
      existing_configuration_preserved: true,
      post_init_verified: true,
      recovery_category: "none",
    });
    const a = repositoryInitializationResultToStableDict(result);
    const b = repositoryInitializationResultToStableDict(result);
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    const diag = diagnosticsFromResult(result);
    const blob = repositoryInitializationDiagnosticsToStableDict(diag);
    assert.deepEqual(repoInitDiagnosticsContainForbiddenKeys(blob), []);
    assert.equal(JSON.stringify(blob).includes("stdout"), false);
    assert.ok(userMessageForInitResult(result).length > 0);
  });
});

describe("force overwrite boundary", () => {
  it("buildInitArgs never includes --force", () => {
    const args = buildInitArgs(DEFAULT_SETTINGS);
    assert.deepEqual(args, ["init"]);
    assertInitArgsForbidForce(args);
    assert.throws(
      () => assertInitArgsForbidForce(["init", "--force"]),
      /force_overwrite_forbidden/
    );
  });
});

describe("workflow + telemetry boundaries for init", () => {
  it("allows validating_workspace → completed for early init exits", () => {
    assert.equal(canTransition("validating_workspace", "completed"), true);
    assert.equal(canTransition("validating_workspace", "initializing"), true);
    assert.equal(canTransition("initializing", "awaiting_consent"), false);
    assert.equal(canTransition("initializing", "running_assessment"), false);
  });

  it("marks codestrata.init ineligible for telemetry consent", () => {
    assert.ok(
      (EXCLUDED_TELEMETRY_COMMANDS as readonly string[]).includes(
        "codestrata.init"
      )
    );
  });
});

describe("idempotency via Approach A", () => {
  it("second init plan skips CLI and preserves config bytes", () => {
    const root = tempDir();
    try {
      const cfg = path.join(root, "codestrata.toml");
      const body = "[repository]\npath = \".\"\n# user note\n";
      fs.writeFileSync(cfg, body, "utf8");
      const before = fs.readFileSync(cfg);
      const first = planRepositoryInitialization(
        detectRepositoryInitState({ workspaceRoot: root }).state
      );
      assert.equal(first.action, "skip_already_initialized");
      const second = planRepositoryInitialization(
        detectRepositoryInitState({ workspaceRoot: root }).state
      );
      assert.equal(second.action, "skip_already_initialized");
      assert.deepEqual(fs.readFileSync(cfg), before);
    } finally {
      fs.rmSync(root, { recursive: true, force: true });
    }
  });
});
