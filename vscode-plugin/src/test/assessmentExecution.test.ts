/**
 * Slice 13.5 assessment-execution unit tests.
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { buildAssessArgs } from "../engine/cliContract";
import { DEFAULT_SETTINGS } from "../config/settings";
import {
  ASSESSMENT_EXECUTION_POLICY_ID,
  ASSESSMENT_EXECUTION_POLICY_VERSION,
  assertSingleAssessInvocationArgs,
  assessmentDiagnosticsContainForbiddenKeys,
  assessmentExecutionDiagnosticsToStableDict,
  assessmentExecutionPolicyToStableDict,
  assessmentExecutionResultToStableDict,
  createAssessmentExecutionPolicy,
  diagnosticsFromAssessmentResult,
  planAssessmentReadiness,
  resultAfterEngineAssessment,
  resultForCliUnavailable,
  resultForReadinessFailure,
} from "../assessmentExecution";
import { canTransition } from "../communityWorkflow";
import { ELIGIBLE_TELEMETRY_COMMANDS } from "../telemetry/promptPolicy";

describe("assessment execution policy", () => {
  it("serializes deterministically without paths or timestamps", () => {
    const a = assessmentExecutionPolicyToStableDict(
      createAssessmentExecutionPolicy()
    );
    const b = assessmentExecutionPolicyToStableDict(
      createAssessmentExecutionPolicy()
    );
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.policy_id, ASSESSMENT_EXECUTION_POLICY_ID);
    assert.equal(a.policy_version, ASSESSMENT_EXECUTION_POLICY_VERSION);
    assert.equal(a.standard_product_invocation_count, 1);
    assert.equal(a.ai_product_invocation_count, 1);
    assert.equal(a.silent_fallback_allowed, false);
    assert.equal(a.initialized_repository_required, true);
    assert.equal(a.command_determines_ai_mode, true);
    assert.equal(JSON.stringify(a).includes("/Users/"), false);
    assert.equal(JSON.stringify(a).includes("timestamp"), false);
  });
});

describe("assessment readiness ordering", () => {
  it("blocks assessment until repository is initialized", () => {
    assert.equal(
      planAssessmentReadiness("initialized").action,
      "continue_to_cli_discovery"
    );
    assert.equal(
      planAssessmentReadiness("not_initialized").action,
      "fail_not_initialized"
    );
    assert.equal(
      planAssessmentReadiness("invalid_configuration").action,
      "fail_invalid_configuration"
    );
    assert.equal(
      planAssessmentReadiness("partial_initialization").action,
      "fail_partial_configuration"
    );
    const blocked = resultForReadinessFailure(
      "run_assessment",
      false,
      planAssessmentReadiness("not_initialized") as Exclude<
        ReturnType<typeof planAssessmentReadiness>,
        { action: "continue_to_cli_discovery" }
      >
    );
    assert.equal(blocked.product_invocation_count, 0);
    assert.equal(blocked.consent_category, "not_reached");
    assert.equal(blocked.recovery_category, "initialize_repository");
  });

  it("does not reach consent when CLI unavailable", () => {
    const r = resultForCliUnavailable("run_assessment_with_ai", true);
    assert.equal(r.consent_category, "not_reached");
    assert.equal(r.product_invocation_count, 0);
    assert.equal(r.ai_requested, true);
  });
});

describe("engine assessment results", () => {
  it("treats CLI exit as primary and report missing as postcondition", () => {
    const ok = resultAfterEngineAssessment({
      operation: "run_assessment",
      aiRequested: false,
      consent: "denied",
      cli: { exitCode: 0, cancelled: false, reportAvailable: true },
    });
    assert.equal(ok.status, "success");
    assert.equal(ok.primary_exit_category, "success");
    assert.equal(ok.product_invocation_count, 1);

    const missing = resultAfterEngineAssessment({
      operation: "run_assessment",
      aiRequested: false,
      consent: "allowed_for_session",
      cli: { exitCode: 0, cancelled: false, reportAvailable: false },
    });
    assert.equal(missing.status, "report_missing");
    assert.equal(missing.primary_exit_category, "success");
    assert.equal(missing.report_available, false);

    const fail = resultAfterEngineAssessment({
      operation: "run_assessment_with_ai",
      aiRequested: true,
      consent: "denied",
      cli: { exitCode: 1, cancelled: false, reportAvailable: false },
    });
    assert.equal(fail.status, "failure");
    assert.equal(fail.primary_exit_category, "failure");

    const cancelled = resultAfterEngineAssessment({
      operation: "run_assessment",
      aiRequested: false,
      consent: "denied",
      cli: { exitCode: 0, cancelled: true, reportAvailable: false },
    });
    assert.equal(cancelled.status, "cancelled");
    assert.equal(cancelled.cancellation_category, "user_cancelled");
  });

  it("keeps diagnostics privacy-safe", () => {
    const result = resultAfterEngineAssessment({
      operation: "run_assessment",
      aiRequested: false,
      consent: "denied",
      cli: { exitCode: 0, cancelled: false, reportAvailable: true },
    });
    const diag = diagnosticsFromAssessmentResult(result, true);
    const blob = assessmentExecutionDiagnosticsToStableDict(diag);
    assert.deepEqual(assessmentDiagnosticsContainForbiddenKeys(blob), []);
    assert.equal(
      JSON.stringify(assessmentExecutionResultToStableDict(result)).includes(
        "stdout"
      ),
      false
    );
  });
});

describe("CLI argument contract", () => {
  it("builds one standard and one AI assess invocation", () => {
    const standard = buildAssessArgs({
      workspaceFolder: "/tmp/repo",
      withAi: false,
      settings: DEFAULT_SETTINGS,
    });
    assert.equal(standard[0], "assess");
    assert.ok(standard.includes("--no-ai"));
    assert.equal(standard.includes("--with-ai"), false);
    assertSingleAssessInvocationArgs(standard);

    const ai = buildAssessArgs({
      workspaceFolder: "/tmp/repo",
      withAi: true,
      settings: DEFAULT_SETTINGS,
    });
    assert.ok(ai.includes("--with-ai"));
    assert.equal(ai.includes("--no-ai"), false);
    assertSingleAssessInvocationArgs(ai);

    assert.throws(
      () => assertSingleAssessInvocationArgs(["assess", "assess", "--no-ai"]),
      /duplicate_assess/
    );
    assert.throws(
      () => assertSingleAssessInvocationArgs(["assess", "--no-ai", "init"]),
      /forbidden_fallback/
    );
  });
});

describe("workflow + telemetry boundaries for assessment", () => {
  it("never routes assessment through initializing", () => {
    assert.equal(canTransition("validating_workspace", "awaiting_consent"), true);
    assert.equal(canTransition("initializing", "running_assessment"), false);
    assert.equal(canTransition("awaiting_consent", "running_assessment"), true);
  });

  it("keeps only assess commands telemetry-eligible", () => {
    assert.deepEqual([...ELIGIBLE_TELEMETRY_COMMANDS], [
      "codestrata.assess",
      "codestrata.assessWithAi",
    ]);
  });
});
