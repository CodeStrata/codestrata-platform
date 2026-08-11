/**
 * Slice 13.9 telemetry consent integration unit tests.
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  TELEMETRY_INTEGRATION_POLICY_ID,
  TELEMETRY_INTEGRATION_POLICY_VERSION,
  TELEMETRY_RUNTIME_POLICY_REF,
  assertConsentMayProceed,
  assertFreshConsentDecision,
  createIntegrationDiagnostics,
  createTelemetryIntegrationPolicy,
  eligibilityMapToStableDict,
  evaluateConsentOrdering,
  integrationDiagnosticsContainForbiddenKeys,
  integrationDiagnosticsToStableDict,
  isTelemetryEligibleCommand,
  readinessStageOrder,
  telemetryIntegrationPolicyToStableDict,
  TelemetryConsentIntegrationError,
} from "../telemetryConsentIntegration";
import {
  COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_URN,
  ELIGIBLE_TELEMETRY_COMMANDS,
  EXCLUDED_TELEMETRY_COMMANDS,
} from "../telemetry";
import { RECOVERY_ACTION_LABELS } from "../failureRecovery";

describe("telemetry integration policy", () => {
  it("serializes deterministically and references runtime 2.0", () => {
    const a = telemetryIntegrationPolicyToStableDict(
      createTelemetryIntegrationPolicy()
    );
    const b = telemetryIntegrationPolicyToStableDict(
      createTelemetryIntegrationPolicy()
    );
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.policy_id, TELEMETRY_INTEGRATION_POLICY_ID);
    assert.equal(a.policy_version, TELEMETRY_INTEGRATION_POLICY_VERSION);
    assert.equal(a.telemetry_runtime_policy_version, "2.0");
    assert.equal(
      COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_URN,
      "community-vscode-telemetry-runtime-policy:2.0"
    );
    assert.ok(TELEMETRY_RUNTIME_POLICY_REF.includes("2.0"));
    assert.equal(a.persistence_allowed, true);
    assert.equal(a.prior_consent_reuse_allowed, true);
    assert.equal(a.machine_identity_allowed, false);
    assert.equal(a.activation_eligible, false);
    assert.equal(a.recovery_eligible, false);
    assert.deepEqual(a.eligible_operations, [
      "run_assessment",
      "run_assessment_with_ai",
    ]);
  });
});

describe("eligibility", () => {
  it("only assess commands are eligible", () => {
    assert.equal(isTelemetryEligibleCommand("codestrata.assess"), true);
    assert.equal(isTelemetryEligibleCommand("codestrata.assessWithAi"), true);
    assert.equal(isTelemetryEligibleCommand("codestrata.init"), false);
    assert.equal(isTelemetryEligibleCommand("codestrata.openHtmlReport"), false);
    assert.equal(isTelemetryEligibleCommand("codestrata.installEngine"), false);
    assert.equal(isTelemetryEligibleCommand("activation"), false);
    assert.deepEqual(
      [...ELIGIBLE_TELEMETRY_COMMANDS].sort(),
      ["codestrata.assess", "codestrata.assessWithAi"]
    );
    assert.ok(EXCLUDED_TELEMETRY_COMMANDS.includes("codestrata.init"));
    assert.ok(EXCLUDED_TELEMETRY_COMMANDS.includes("codestrata.openHtmlReport"));
    const map = eligibilityMapToStableDict();
    assert.equal(JSON.stringify(map).includes("/Users/"), false);
  });

  it("recovery action labels other than re-assess are ineligible surfaces", () => {
    assert.equal(
      RECOVERY_ACTION_LABELS.open_report,
      "Open Report"
    );
    assert.equal(
      isTelemetryEligibleCommand("codestrata.openHtmlReport"),
      false
    );
    assert.equal(isTelemetryEligibleCommand("codestrata.init"), false);
  });
});

describe("readiness ordering", () => {
  it("blocks consent until readiness passes", () => {
    assert.equal(
      evaluateConsentOrdering({
        workspace_ready: false,
        repository_initialized: true,
        cli_compatible: true,
        ai_confirmation_satisfied: true,
      }).consent_allowed,
      false
    );
    assert.equal(
      evaluateConsentOrdering({
        workspace_ready: true,
        repository_initialized: false,
        cli_compatible: true,
        ai_confirmation_satisfied: true,
      }).reason,
      "repository_not_initialized"
    );
    assert.equal(
      evaluateConsentOrdering({
        workspace_ready: true,
        repository_initialized: true,
        cli_compatible: false,
        ai_confirmation_satisfied: true,
      }).reason,
      "cli_not_ready"
    );
    assert.equal(
      evaluateConsentOrdering({
        workspace_ready: true,
        repository_initialized: true,
        cli_compatible: true,
        ai_confirmation_satisfied: false,
      }).reason,
      "ai_confirmation_declined"
    );
    assert.equal(
      evaluateConsentOrdering({
        workspace_ready: true,
        repository_initialized: true,
        cli_compatible: true,
        ai_confirmation_satisfied: true,
      }).consent_allowed,
      true
    );
    assert.deepEqual(readinessStageOrder()[0], "workspace");
    assert.ok(readinessStageOrder().includes("telemetry_consent"));
  });

  it("assertConsentMayProceed enforces ordering", () => {
    assert.throws(
      () =>
        assertConsentMayProceed({
          commandId: "codestrata.init",
          readiness: {
            workspace_ready: true,
            repository_initialized: true,
            cli_compatible: true,
            ai_confirmation_satisfied: true,
          },
        }),
      TelemetryConsentIntegrationError
    );
    assert.throws(
      () =>
        assertConsentMayProceed({
          commandId: "codestrata.assess",
          readiness: {
            workspace_ready: true,
            repository_initialized: false,
            cli_compatible: true,
            ai_confirmation_satisfied: true,
          },
        }),
      (err: unknown) =>
        err instanceof TelemetryConsentIntegrationError &&
        err.code === "repository_not_initialized"
    );
    assert.doesNotThrow(() =>
      assertConsentMayProceed({
        commandId: "codestrata.assess",
        readiness: {
          workspace_ready: true,
          repository_initialized: true,
          cli_compatible: true,
          ai_confirmation_satisfied: true,
        },
      })
    );
  });
});

describe("fresh consent", () => {
  it("allows explicit local preference reuse while forbidding identity reuse", () => {
    assert.doesNotThrow(() =>
      assertFreshConsentDecision({
        priorConsentReused: false,
        persisted: false,
      })
    );
    assert.doesNotThrow(() =>
      assertFreshConsentDecision({
        priorConsentReused: true,
        persisted: true,
        source: "persisted_preference",
      })
    );
    assert.doesNotThrow(() =>
      assertFreshConsentDecision({
        priorConsentReused: false,
        persisted: true,
        source: "interactive_prompt",
      })
    );
    assert.throws(
      () =>
        assertFreshConsentDecision({
          priorConsentReused: true,
          persisted: false,
        }),
      TelemetryConsentIntegrationError
    );
    assert.throws(
      () =>
        assertFreshConsentDecision({
          priorConsentReused: false,
          persisted: true,
        }),
      TelemetryConsentIntegrationError
    );
  });
});

describe("integration diagnostics privacy", () => {
  it("omits forbidden keys and paths", () => {
    const d = integrationDiagnosticsToStableDict(
      createIntegrationDiagnostics({
        operation: "run_assessment",
        eligible: true,
        ordering: {
          readiness_passed: true,
          consent_allowed: true,
          blocked_stage: "none",
          reason: "ready",
        },
        consentPromptAttempted: true,
        consentPromptCount: 1,
        consentDecisionCategory: "allowed_for_session",
        telemetryRuntimeCreated: true,
        telemetryTransportCategory: "unavailable",
        analyticsConstructed: true,
        analyticsSinkCategory: "unavailable",
        limitations: createTelemetryIntegrationPolicy().limitations,
      })
    );
    assert.equal(integrationDiagnosticsContainForbiddenKeys(d), false);
    assert.equal(d.consent_reused, false);
    assert.equal(d.persisted, false);
    assert.equal(d.identity_used, false);
    assert.equal(JSON.stringify(d).includes("timestamp"), false);
  });
});
