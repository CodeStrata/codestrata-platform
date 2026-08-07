/**
 * Slice 13.1 Community workflow contract unit tests.
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  ALLOWED_TRANSITIONS,
  COMMAND_TO_OPERATION,
  COMPATIBILITY_ALIASES,
  CommunityWorkflowSession,
  WORKFLOW_COMMAND_IDS,
  WORKFLOW_OPERATIONS,
  WORKFLOW_POLICY_ID,
  WORKFLOW_POLICY_VERSION,
  WORKFLOW_STATES,
  assertTransition,
  canTransition,
  classifyWorkspaceKind,
  createWorkflowPolicy,
  diagnosticsContainForbiddenKeys,
  mapConsentToDecisionCategory,
  operationForCommand,
  workflowDiagnosticsToStableDict,
  workflowPolicyToStableDict,
  communityWorkflowResultToStableDict,
} from "../communityWorkflow";
import { WorkflowTransitionError } from "../communityWorkflow/errors";

describe("community workflow policy", () => {
  it("serializes deterministically without paths or timestamps", () => {
    const a = workflowPolicyToStableDict(createWorkflowPolicy());
    const b = workflowPolicyToStableDict(createWorkflowPolicy());
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.policy_id, WORKFLOW_POLICY_ID);
    assert.equal(a.policy_version, WORKFLOW_POLICY_VERSION);
    assert.equal(a.cli_invocation_count, 1);
    assert.equal(a.installation_automation_available, false);
    assert.equal(a.compatibility_detection_available, false);
    const text = JSON.stringify(a);
    assert.equal(text.includes("/Users/"), false);
    assert.equal(text.includes("timestamp"), false);
  });
});

describe("community workflow operations", () => {
  it("maps workflow commands to operations", () => {
    assert.equal(operationForCommand("codestrata.assess"), "run_assessment");
    assert.equal(
      operationForCommand("codestrata.assessWithAi"),
      "run_assessment_with_ai"
    );
    assert.equal(operationForCommand("codestrata.init"), "initialize_repository");
    assert.equal(operationForCommand("codestrata.openHtmlReport"), "open_report");
    assert.equal(operationForCommand("codestrata.doctor"), undefined);
    assert.equal(WORKFLOW_COMMAND_IDS.length, 4);
    assert.equal(WORKFLOW_OPERATIONS.length, 4);
    assert.equal(Object.keys(COMMAND_TO_OPERATION).length, 4);
    assert.equal(COMPATIBILITY_ALIASES[0]?.alias, "codestrata.doctor");
  });
});

describe("community workflow transitions", () => {
  it("allows known edges and rejects invalid ones", () => {
    assert.equal(canTransition("idle", "validating_workspace"), true);
    assert.equal(canTransition("validating_workspace", "completed"), true);
    assert.equal(canTransition("running_assessment", "completed"), true);
    assert.equal(canTransition("idle", "running_assessment"), false);
    assert.throws(
      () => assertTransition("idle", "running_assessment"),
      (error: unknown) => error instanceof WorkflowTransitionError
    );
    for (const state of WORKFLOW_STATES) {
      assert.ok(Array.isArray(ALLOWED_TRANSITIONS[state]));
    }
  });
});

describe("community workflow session", () => {
  it("records a single CLI invocation and closes progress on success", () => {
    const session = new CommunityWorkflowSession({
      operation: "run_assessment",
      aiRequested: false,
    });
    session.transitionTo("validating_workspace");
    session.transitionTo("awaiting_consent");
    session.setTelemetryDecision(
      mapConsentToDecisionCategory({
        decision: "denied",
        prompted: true,
        interactive: true,
      })
    );
    session.transitionTo("running_assessment");
    session.markProgressStarted();
    session.recordCliInvocation();
    assert.equal(session.getCliInvocationCount(), 1);
    session.markProgressClosed();
    session.transitionTo("locating_report");
    session.setReportAvailable(true);
    const result = session.complete({
      status: "success",
      primaryExit: "success",
      resultCategory: "ok",
    });
    assert.equal(result.status, "success");
    assert.equal(result.primary_exit_category, "success");
    assert.equal(session.getCliInvocationCount(), 1);
    const diag = session.diagnostics();
    assert.equal(diag.progress_started, true);
    assert.equal(diag.progress_closed, true);
    assert.equal(diag.cli_invocation_count, 1);
    assert.equal(diag.primary_result_preserved, true);
    const stable = workflowDiagnosticsToStableDict(diag);
    assert.deepEqual(diagnosticsContainForbiddenKeys(stable), []);
    assert.equal(JSON.stringify(stable).includes("/Users/"), false);
  });

  it("keeps assessment success when report open fails", () => {
    const session = new CommunityWorkflowSession({
      operation: "run_assessment",
      aiRequested: false,
    });
    session.transitionTo("validating_workspace");
    session.transitionTo("awaiting_consent");
    session.transitionTo("running_assessment");
    session.recordCliInvocation();
    session.markProgressStarted();
    session.markProgressClosed();
    session.transitionTo("locating_report");
    session.setReportAvailable(true);
    session.transitionTo("opening_report");
    const result = session.complete({
      status: "success",
      primaryExit: "success",
      reportOpenFailed: true,
    });
    assert.equal(result.status, "success");
    assert.equal(result.primary_exit_category, "success");
    assert.equal(result.result_category, "report_open_failed");
    assert.equal(session.diagnostics().primary_result_preserved, true);
  });

  it("closes progress on cancellation", () => {
    const session = new CommunityWorkflowSession({
      operation: "run_assessment_with_ai",
      aiRequested: true,
    });
    session.transitionTo("validating_workspace");
    session.transitionTo("awaiting_consent");
    session.transitionTo("running_assessment");
    session.markProgressStarted();
    session.recordCliInvocation();
    const result = session.complete({
      status: "cancelled",
      resultCategory: "assessment_cancelled",
      primaryExit: "cancelled",
    });
    assert.equal(result.status, "cancelled");
    assert.equal(session.diagnostics().progress_closed, true);
  });

  it("serializes results deterministically", () => {
    const session = new CommunityWorkflowSession({
      operation: "initialize_repository",
      cancellationSupported: false,
    });
    session.transitionTo("validating_workspace");
    session.transitionTo("initializing");
    session.recordCliInvocation();
    const result = session.complete({
      status: "success",
      primaryExit: "success",
      resultCategory: "ok",
    });
    const a = communityWorkflowResultToStableDict(result);
    const b = communityWorkflowResultToStableDict(result);
    assert.equal(JSON.stringify(a), JSON.stringify(b));
  });
});

describe("workspace eligibility", () => {
  it("classifies folder counts", () => {
    assert.equal(classifyWorkspaceKind({ folderCount: 0 }), "no_workspace");
    assert.equal(classifyWorkspaceKind({ folderCount: 1 }), "folder_workspace");
    assert.equal(classifyWorkspaceKind({ folderCount: 3 }), "multi_root_workspace");
  });
});
