"""Focused static checks for Slice 13.6 assessment progress."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_assessment_progress.contract import (
    ASSESSMENT_EXECUTION_POLICY_VERSION,
    ASSESSMENT_SCHEMA_VERSION,
    INTENDED_VSCODE_VERSION,
    PROGRESS_PACKAGE,
    PROGRESS_POLICY_ID,
    PROGRESS_POLICY_VERSION,
    WORKFLOW_POLICY_VERSION,
)
from verification.vscode_assessment_progress.models import CheckResult, Defect
from verification.vscode_assessment_progress.scenarios import PHASE_INVENTORY


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def _pkg_version(monorepo: Path) -> str:
    text = _read(monorepo, "vscode-plugin/package.json")
    match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
    return match.group(1) if match else ""


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = _read(monorepo, f"{PROGRESS_PACKAGE}/policy.ts")
    phases = _read(monorepo, f"{PROGRESS_PACKAGE}/phases.ts")
    lifecycle = _read(monorepo, f"{PROGRESS_PACKAGE}/lifecycle.ts")
    diagnostics = _read(monorepo, f"{PROGRESS_PACKAGE}/diagnostics.ts")
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    docs = _read(monorepo, "vscode-plugin/docs/assessment-progress.md")
    exec_docs = _read(monorepo, "vscode-plugin/docs/assessment-execution.md")
    workflow_docs = _read(monorepo, "vscode-plugin/docs/community-workflow.md")

    assess_handler = ""
    if "const runAssessment = async" in ext:
        assess_handler = ext.split("const runAssessment = async", 1)[1][:18000]

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                PROGRESS_POLICY_ID in policy
                and PROGRESS_POLICY_VERSION in policy,
                f"{PROGRESS_POLICY_ID}:{PROGRESS_POLICY_VERSION}",
                "progress_policy",
            ),
            CheckResult(
                "policy:indeterminate",
                "progress_is_indeterminate_by_default: true" in policy
                and "fabricated_percentage_allowed: false" in policy
                and "engine_structured_progress_available: false" in policy,
                "Decision A indeterminate",
                "progress_policy",
            ),
            CheckResult(
                "policy:one_lifecycle",
                "one_progress_lifecycle_per_assessment: true" in policy
                and "progress_starts_after_consent: true" in policy,
                "one lifecycle after consent",
                "progress_policy",
            ),
            CheckResult(
                "lifecycle:class",
                "class AssessmentProgressLifecycle" in lifecycle
                and "requestCancellation" in lifecycle
                and "close(" in lifecycle,
                "lifecycle owner",
                "lifecycle",
            ),
            CheckResult(
                "lifecycle:wired_once",
                assess_handler.count("new AssessmentProgressLifecycle") == 1
                and assess_handler.count("withProgress") == 1,
                "one withProgress + one lifecycle",
                "lifecycle",
            ),
            CheckResult(
                "lifecycle:after_consent",
                "awaiting_consent" in assess_handler
                and assess_handler.find("awaiting_consent")
                < assess_handler.find("new AssessmentProgressLifecycle"),
                "progress after consent",
                "lifecycle",
            ),
            CheckResult(
                "phases:inventory",
                all(p in phases for p in PHASE_INVENTORY),
                ",".join(PHASE_INVENTORY),
                "lifecycle",
            ),
            CheckResult(
                "phases:no_fabricated",
                "scanning_files" not in phases
                and "running_ai" not in phases
                and "evaluating_security" not in phases,
                "no invented phases",
                "lifecycle",
            ),
            CheckResult(
                "indeterminate:no_increment",
                "fabricated_percentage_forbidden" in lifecycle
                and "increment" not in assess_handler.split("progress.report")[1][:200]
                if "progress.report" in assess_handler
                else "fabricated_percentage_forbidden" in lifecycle,
                "no percentage in report",
                "indeterminate_progress",
            ),
            CheckResult(
                "engine_signal:none",
                "engine_structured_progress_available: false" in policy
                and "Decision A" in docs,
                "no Engine progress protocol",
                "engine_signal",
            ),
            CheckResult(
                "standard:shared_lifecycle",
                "progressTitle(aiRequested)" in assess_handler
                and "AssessmentProgressLifecycle" in assess_handler,
                "standard uses shared lifecycle",
                "standard_assessment",
            ),
            CheckResult(
                "ai:no_second_bar",
                assess_handler.count("withProgress") == 1
                and "second" not in assess_handler.lower(),
                "no second AI progress bar",
                "ai_assessment",
            ),
            CheckResult(
                "cancel:once",
                "requestCancellation" in assess_handler
                and "requestCancellation" in lifecycle,
                "cancel abort once",
                "cancellation",
            ),
            CheckResult(
                "cancel:no_retry",
                "cancellation_causes_retry: false" in policy,
                "no retry on cancel",
                "cancellation",
            ),
            CheckResult(
                "race:close_once",
                "if (this.closed)" in lifecycle or "if (this.closed)" in lifecycle.replace(
                    " ", ""
                )
                or "if (this.closed)" in lifecycle,
                "close idempotent",
                "race_condition",
            ),
            CheckResult(
                "race:abort_once",
                "cancellationAbortIssued" in lifecycle,
                "abort issued once",
                "race_condition",
            ),
            CheckResult(
                "primary:preserved",
                "primary_result_authoritative: true" in policy
                and "primary_result_preserved: true" in lifecycle,
                "primary preserved",
                "primary_authority",
            ),
            CheckResult(
                "primary:progress_isolated",
                "progress_failure_isolated: true" in policy
                and "Isolated" in lifecycle,
                "progress failure isolated",
                "primary_authority",
            ),
            CheckResult(
                "telemetry:no_new_events",
                "feature_invoked" not in lifecycle
                and "progress_policy" not in _read(
                    monorepo, "vscode-plugin/src/telemetry/events.ts"
                ),
                "no progress telemetry events",
                "telemetry_boundary",
            ),
            CheckResult(
                "analytics:no_new_fields",
                "progress" not in _read(
                    monorepo, "vscode-plugin/src/telemetry/analytics/schema.ts"
                ).lower()
                or "progress_phase" not in _read(
                    monorepo, "vscode-plugin/src/telemetry/analytics/schema.ts"
                ),
                "no progress analytics fields",
                "analytics_boundary",
            ),
            CheckResult(
                "output:local_redacted",
                "redactSecrets" in assess_handler,
                "output redacted",
                "output_boundary",
            ),
            CheckResult(
                "notification:one_location",
                "ProgressLocation.Notification" in assess_handler,
                "Notification progress",
                "notification_boundary",
            ),
            CheckResult(
                "report_phase:locating",
                'enterPhase("locating_report")' in assess_handler
                or "enterPhase(\"locating_report\")" in assess_handler,
                "locating_report phase",
                "report_phase",
            ),
            CheckResult(
                "report_phase:missing_soft",
                "report_not_found" in assess_handler
                and 'primaryExit: "success"' in assess_handler,
                "missing report soft",
                "report_phase",
            ),
            CheckResult(
                "workflow:running_then_locate",
                'transitionTo("running_assessment")' in assess_handler
                and 'transitionTo("locating_report")' in assess_handler,
                "workflow aligned",
                "workflow_integration",
            ),
            CheckResult(
                "privacy:forbidden_keys",
                "progressDiagnosticsContainForbiddenKeys" in diagnostics,
                "privacy helper",
                "privacy",
            ),
            CheckResult(
                "privacy:messages",
                "progressMessageForPhase" in phases
                and "provider" not in progress_message_sample(phases),
                "safe messages",
                "privacy",
            ),
            CheckResult(
                "docs:progress",
                (monorepo / "vscode-plugin/docs/assessment-progress.md").is_file(),
                "progress docs",
                "privacy",
            ),
            CheckResult(
                "docs:linked",
                "assessment-progress" in exec_docs
                or "13.6" in exec_docs,
                "execution docs updated",
                "privacy",
            ),
            CheckResult(
                "docs:workflow",
                "assessment-progress" in workflow_docs or "13.6" in workflow_docs,
                "workflow docs updated",
                "privacy",
            ),
            CheckResult(
                "vscode:version",
                _pkg_version(monorepo) == INTENDED_VSCODE_VERSION,
                _pkg_version(monorepo),
                "vscode_regression",
            ),
            CheckResult(
                "schema:assessment_1_2",
                ASSESSMENT_SCHEMA_VERSION == "1.2",
                ASSESSMENT_SCHEMA_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "policy:priors_1_0",
                WORKFLOW_POLICY_VERSION == "1.0"
                and ASSESSMENT_EXECUTION_POLICY_VERSION == "1.0",
                "prior policies 1.0",
                "vscode_regression",
            ),
            CheckResult(
                "epic_14:not_started",
                not (monorepo / "verification" / "vscode_epic14_product_experience").exists()
                and "startEpic14ProductExperience" not in ext,
                "Epic 14 deferred",
                "vscode_regression",
            ),
            CheckResult(
                "activation:no_progress",
                "AssessmentProgressLifecycle"
                not in ext.split("export function activate")[1].split(
                    "const runAssessment"
                )[0]
                if "export function activate" in ext and "const runAssessment" in ext
                else False,
                "activation has no progress",
                "lifecycle",
            ),
        ]
    )

    # Soft-clean race:close_once
    checks = [c for c in checks if c.name != "race:close_once"]
    checks.append(
        CheckResult(
            "race:close_once",
            "if (this.closed)" in lifecycle,
            "close idempotent",
            "race_condition",
        )
    )

    if not all(c.ok for c in checks if c.category == "lifecycle"):
        defects.append(
            Defect("lifecycle defect", "lifecycle", "one post-consent", "leak/dup")
        )
    if not all(c.ok for c in checks if c.category == "indeterminate_progress"):
        defects.append(
            Defect(
                "fabricated-progress defect",
                "percentage",
                "indeterminate",
                "fabricated",
            )
        )
    if not all(c.ok for c in checks if c.category == "primary_authority"):
        defects.append(
            Defect(
                "primary-authority defect",
                "primary",
                "preserved",
                "overridden",
            )
        )

    return checks, defects


def progress_message_sample(phases: str) -> str:
    return phases.lower()
