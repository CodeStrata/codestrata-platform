/**
 * Slice 13.8 failure-recovery unit tests.
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  FAILURE_DOMAINS,
  RECOVERY_ACTIONS,
  RECOVERY_ACTION_LABELS,
  RECOVERY_POLICY_ID,
  RECOVERY_POLICY_VERSION,
  createFailureRecoveryPolicy,
  failureRecoveryPolicyToStableDict,
  failureRecoveryResultToStableDict,
  failureRecoveryDiagnosticsToStableDict,
  diagnosticsFromGuidance,
  recoveryDiagnosticsContainForbiddenKeys,
  resolveRecoveryGuidance,
  knownFailureCategories,
  presentFailureRecovery,
  isSecondaryFailureCategory,
  type RecoveryNotificationHost,
} from "../failureRecovery";

function mockHost(options?: {
  choice?: string | undefined;
  failExecute?: boolean;
}): RecoveryNotificationHost & {
  messages: string[];
  executed: string[];
} {
  const messages: string[] = [];
  const executed: string[] = [];
  return {
    messages,
    executed,
    showErrorMessage: async (message, ..._actions) => {
      messages.push(message);
      return options?.choice;
    },
    showWarningMessage: async (message, ..._actions) => {
      messages.push(message);
      return options?.choice;
    },
    showInformationMessage: async (message, ..._actions) => {
      messages.push(message);
      return options?.choice;
    },
    executeCommand: async (commandId) => {
      if (options?.failExecute) {
        throw new Error("dispatch failed");
      }
      executed.push(commandId);
    },
  };
}

describe("failure recovery policy", () => {
  it("serializes deterministically with auto-execute forbidden", () => {
    const a = failureRecoveryPolicyToStableDict(createFailureRecoveryPolicy());
    const b = failureRecoveryPolicyToStableDict(createFailureRecoveryPolicy());
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.policy_id, RECOVERY_POLICY_ID);
    assert.equal(a.policy_version, RECOVERY_POLICY_VERSION);
    assert.equal(a.automatic_recovery_execution_allowed, false);
    assert.equal(a.automatic_retry_allowed, false);
    assert.equal(a.automatic_install_allowed, false);
    assert.equal(a.automatic_assessment_rerun_allowed, false);
    assert.equal(a.telemetry_allowed, false);
    assert.equal(a.analytics_allowed, false);
    assert.equal(JSON.stringify(a).includes("/Users/"), false);
  });
});

describe("catalog coverage", () => {
  it("covers inventory domains and actions", () => {
    assert.ok(FAILURE_DOMAINS.includes("workspace"));
    assert.ok(FAILURE_DOMAINS.includes("secondary_failure"));
    assert.ok(RECOVERY_ACTIONS.includes("initialize_repository"));
    assert.equal(
      RECOVERY_ACTION_LABELS.initialize_repository,
      "Initialize Repository"
    );
    const cats = knownFailureCategories();
    assert.ok(cats.includes("assessment_failed"));
    assert.ok(cats.includes("report_not_found"));
    assert.ok(isSecondaryFailureCategory("report_open_failed"));
    assert.equal(isSecondaryFailureCategory("assessment_failed"), false);
  });

  it("maps failures to what/why/next without paths", () => {
    const g = resolveRecoveryGuidance("repository_not_initialized");
    assert.equal(g.recovery_action, "initialize_repository");
    assert.equal(g.auto_execute, false);
    assert.equal(g.workflow_recovery_flag, "user_action_available");
    assert.ok(g.what_failed.length > 0);
    assert.ok(g.why_failed.length > 0);
    assert.ok(g.next_step.length > 0);
    assert.equal(g.user_message.includes("/Users/"), false);
    assert.equal(g.user_message.includes("file://"), false);
  });
});

describe("presentation", () => {
  it("does not auto-execute recovery", async () => {
    const host = mockHost({ choice: undefined });
    const { result } = await presentFailureRecovery({
      failureCategory: "assessment_failed",
      host,
    });
    assert.equal(result.auto_execute, false);
    assert.equal(result.action_dispatched, false);
    assert.equal(host.executed.length, 0);
    assert.equal(result.status, "user_declined");
  });

  it("dispatches only after user selects action", async () => {
    const host = mockHost({
      choice: RECOVERY_ACTION_LABELS.run_assessment_again,
    });
    const { result } = await presentFailureRecovery({
      failureCategory: "assessment_failed",
      host,
    });
    assert.equal(result.status, "user_action_selected");
    assert.equal(result.action_dispatched, true);
    assert.deepEqual(host.executed, ["codestrata.assess"]);
  });

  it("preserves primary success for secondary report failure", async () => {
    const host = mockHost();
    const { guidance, result } = await presentFailureRecovery({
      failureCategory: "report_not_found",
      host,
    });
    assert.equal(guidance.ownership, "secondary");
    assert.equal(result.primary_result_preserved, true);
  });

  it("cancelled assessment has no recovery action", async () => {
    const { guidance, result } = await presentFailureRecovery({
      failureCategory: "assessment_cancelled",
      present: false,
    });
    assert.equal(guidance.recovery_action, "none");
    assert.equal(result.action_dispatched, false);
  });
});

describe("privacy diagnostics", () => {
  it("stable dict omits forbidden keys", async () => {
    const g = resolveRecoveryGuidance("cli_unavailable");
    const d = failureRecoveryDiagnosticsToStableDict(
      diagnosticsFromGuidance(g)
    );
    assert.equal(recoveryDiagnosticsContainForbiddenKeys(d), false);
    const blob = JSON.stringify(d);
    assert.equal(blob.includes("timestamp"), false);
    assert.equal(blob.includes("/Users/"), false);
    assert.equal(blob.includes("file://"), false);
    const { result } = await presentFailureRecovery({
      failureCategory: "cli_unavailable",
      present: false,
    });
    const r = failureRecoveryResultToStableDict(result);
    assert.equal(recoveryDiagnosticsContainForbiddenKeys(r), false);
  });
});
