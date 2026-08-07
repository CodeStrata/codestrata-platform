/**
 * Slice 13.6 assessment-progress unit tests.
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  ASSESSMENT_PROGRESS_POLICY_ID,
  ASSESSMENT_PROGRESS_POLICY_VERSION,
  AssessmentProgressLifecycle,
  assertNoFabricatedPercentage,
  assessmentProgressDiagnosticsToStableDict,
  assessmentProgressPolicyToStableDict,
  assessmentProgressResultToStableDict,
  canTransitionProgress,
  createAssessmentProgressPolicy,
  progressDiagnosticsContainForbiddenKeys,
  progressMessageForPhase,
  progressStatusFromPrimary,
  progressTitle,
} from "../assessmentProgress";

describe("assessment progress policy", () => {
  it("serializes deterministically as indeterminate-by-default", () => {
    const a = assessmentProgressPolicyToStableDict(
      createAssessmentProgressPolicy()
    );
    const b = assessmentProgressPolicyToStableDict(
      createAssessmentProgressPolicy()
    );
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.policy_id, ASSESSMENT_PROGRESS_POLICY_ID);
    assert.equal(a.policy_version, ASSESSMENT_PROGRESS_POLICY_VERSION);
    assert.equal(a.one_progress_lifecycle_per_assessment, true);
    assert.equal(a.progress_starts_after_consent, true);
    assert.equal(a.fabricated_percentage_allowed, false);
    assert.equal(a.engine_structured_progress_available, false);
    assert.equal(a.cancellation_causes_retry, false);
    assert.equal(JSON.stringify(a).includes("timestamp"), false);
    assert.equal(JSON.stringify(a).includes("/Users/"), false);
  });
});

describe("progress phases", () => {
  it("allows only truthful observable transitions", () => {
    assert.equal(canTransitionProgress("running_assessment", "finalizing"), true);
    assert.equal(canTransitionProgress("running_assessment", "locating_report"), true);
    assert.equal(canTransitionProgress("locating_report", "completed"), true);
    assert.equal(canTransitionProgress("completed", "running_assessment"), false);
    assert.equal(
      progressMessageForPhase("running_assessment", false).includes("/"),
      false
    );
    assert.equal(progressTitle(true).includes("optional AI"), true);
  });
});

describe("AssessmentProgressLifecycle", () => {
  it("starts once, updates message-only, closes once", () => {
    const reports: string[] = [];
    const life = new AssessmentProgressLifecycle({
      operation: "run_assessment",
      aiRequested: false,
    });
    life.start({
      report: (v) => reports.push(v.message ?? ""),
    });
    life.start({ report: () => reports.push("dup") }); // no-op
    life.enterPhase("finalizing");
    life.enterPhase("locating_report");
    const first = life.close("completed");
    const second = life.close("failed");
    assert.equal(first.status, "completed");
    assert.equal(second.status, "completed"); // closed once
    assert.equal(life.isClosed(), true);
    assert.ok(life.getUpdateCount() >= 1);
    assert.equal(reports.includes("dup"), false);
  });

  it("issues cancellation abort only once", () => {
    const life = new AssessmentProgressLifecycle({
      operation: "run_assessment_with_ai",
      aiRequested: true,
    });
    life.start();
    assert.equal(life.requestCancellation(), true);
    assert.equal(life.requestCancellation(), false);
    const result = life.close("cancelled");
    assert.equal(result.cancellation_requested, true);
    assert.equal(result.status, "cancelled");
    assert.equal(result.primary_result_preserved, true);
  });

  it("isolates reporter failures from primary result", () => {
    const life = new AssessmentProgressLifecycle({
      operation: "run_assessment",
      aiRequested: false,
    });
    life.start({
      report: () => {
        throw new Error("progress_ui_broken");
      },
    });
    life.enterPhase("finalizing");
    const result = life.close("completed");
    assert.equal(result.status, "completed");
    assert.equal(result.primary_result_preserved, true);
    assert.equal(result.progress_failure_isolated, true);
  });

  it("keeps diagnostics privacy-safe and deterministic", () => {
    const life = new AssessmentProgressLifecycle({
      operation: "run_assessment",
      aiRequested: false,
    });
    life.start();
    life.close("completed");
    const a = assessmentProgressDiagnosticsToStableDict(life.diagnostics());
    const b = assessmentProgressDiagnosticsToStableDict(life.diagnostics());
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.deepEqual(progressDiagnosticsContainForbiddenKeys(a), []);
    assert.equal(
      JSON.stringify(assessmentProgressResultToStableDict(life.toResult())).includes(
        "stdout"
      ),
      false
    );
  });
});

describe("percentage boundary", () => {
  it("forbids fabricated percentage/increment", () => {
    assert.throws(
      () => assertNoFabricatedPercentage({ increment: 10 }),
      /fabricated_percentage_forbidden/
    );
    assert.throws(
      () => assertNoFabricatedPercentage({ percentage: 50 }),
      /fabricated_percentage_forbidden/
    );
    assertNoFabricatedPercentage({});
  });

  it("maps primary outcomes without inventing progress authority", () => {
    assert.equal(progressStatusFromPrimary("success"), "completed");
    assert.equal(progressStatusFromPrimary("failure"), "failed");
    assert.equal(progressStatusFromPrimary("cancelled"), "cancelled");
  });
});
