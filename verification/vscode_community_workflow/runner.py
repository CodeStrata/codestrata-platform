"""Slice 13.1 runner."""

from __future__ import annotations

from pathlib import Path

from verification.vscode_community_workflow import VSCODE_COMMUNITY_WORKFLOW_ID
from verification.vscode_community_workflow.checks import (
    _status,
    check_assessment_cli_boundaries,
    check_commands_and_activation,
    check_documentation,
    check_workflow_package,
)
from verification.vscode_community_workflow.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV131_OUTPUT_RELATIVE,
    WORKFLOW_COMMANDS,
    WORKFLOW_OPERATIONS,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_community_workflow.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeCommunityWorkflowReport,
    report_contains_forbidden_leak,
)
from verification.vscode_community_workflow.scenarios import check_scenarios

WORKFLOW_STATES = [
    "idle",
    "validating_workspace",
    "initializing",
    "awaiting_consent",
    "running_assessment",
    "locating_report",
    "opening_report",
    "completed",
    "failed",
    "cancelled",
]

DEFERRED = [
    "13.3_cli_installation",
    "13.6_progress_ux",
    "13.7_report_opening",
    "14_product_experience",
    "marketplace",
]


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(monorepo: Path) -> VsCodeCommunityWorkflowReport:
    contract = default_contract()
    assert contract.start_slice_13_2 is False

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    buckets: dict[str, list[CheckResult]] = {}

    def take(name: str, pair: tuple[list[CheckResult], list[Defect]]) -> None:
        c, d = pair
        buckets[name] = c
        all_checks.extend(c)
        all_defects.extend(d)

    take("pkg", check_workflow_package(monorepo))
    cmd_checks, cmd_defects, _commands = check_commands_and_activation(monorepo)
    buckets["commands"] = cmd_checks
    all_checks.extend(cmd_checks)
    all_defects.extend(cmd_defects)
    take("assess", check_assessment_cli_boundaries(monorepo))
    take("docs", check_documentation(monorepo))

    limitations = sorted(ALLOWED_LIMITATIONS)

    assess = buckets.get("assess", [])
    take(
        "scenarios",
        check_scenarios(
            monorepo=monorepo,
            activation_ok=all(
                c.ok for c in buckets.get("commands", []) if c.category == "activation"
            ),
            commands_ok=all(
                c.ok
                for c in buckets.get("commands", [])
                if c.category == "command_registration"
            ),
            transitions_ok=all(
                c.ok for c in buckets.get("pkg", []) if c.category == "states"
            ),
            cli_ok=all(c.ok for c in assess if c.category == "cli_invocation"),
            telemetry_ok=all(
                c.ok
                for c in assess
                if c.category in {"telemetry_boundary", "analytics_boundary", "primary_authority"}
            ),
            progress_ok=all(c.ok for c in assess if c.category == "progress_boundary"),
            report_ok=all(c.ok for c in assess if c.category == "report_boundary"),
            privacy_ok=all(c.ok for c in assess if c.category == "privacy"),
            vscode_ok=all(
                c.ok
                for c in buckets.get("commands", []) + assess
                if c.category == "vscode_regression"
            ),
            slice132_absent=all(
                c.ok for c in assess if c.name == "slice_13_2:not_started"
            ),
        ),
    )

    failed = sum(1 for c in all_checks if not c.ok)
    report = VsCodeCommunityWorkflowReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_COMMUNITY_WORKFLOW_ID,
        verdict=_decide(failed, all_defects, limitations),
        command_inventory=list(WORKFLOW_COMMANDS),
        operation_inventory=list(WORKFLOW_OPERATIONS),
        workflow_state_inventory=list(WORKFLOW_STATES),
        workflow_policy_status=_status(
            [c for c in buckets.get("pkg", []) if c.category == "workflow_policy"]
        ),
        command_registration_status=_status(
            [c for c in buckets.get("commands", []) if c.category == "command_registration"]
        ),
        activation_status=_status(
            [c for c in buckets.get("commands", []) if c.category == "activation"]
        ),
        workspace_boundary_status=_status(
            [c for c in assess if c.category == "workspace_boundary"]
        ),
        initialization_boundary_status=_status(
            [c for c in assess if c.category == "initialization"]
        ),
        standard_assessment_status=_status(
            [c for c in assess if c.category == "standard_assessment"]
        ),
        ai_assessment_status=_status(
            [c for c in assess if c.category == "ai_assessment"]
        ),
        cli_invocation_status=_status(
            [c for c in assess if c.category == "cli_invocation"]
        ),
        telemetry_boundary_status=_status(
            [c for c in assess if c.category == "telemetry_boundary"]
        ),
        analytics_boundary_status=_status(
            [c for c in assess if c.category == "analytics_boundary"]
        ),
        progress_boundary_status=_status(
            [c for c in assess if c.category == "progress_boundary"]
        ),
        report_boundary_status=_status(
            [c for c in assess if c.category == "report_boundary"]
        ),
        primary_authority_status=_status(
            [c for c in assess if c.category == "primary_authority"]
        ),
        error_boundary_status=_status(
            [c for c in assess if c.category == "error_boundary"]
        ),
        privacy_status=_status(
            [c for c in assess if c.category == "privacy"]
            + [c for c in buckets.get("docs", [])]
        ),
        vscode_regression_status=_status(
            [
                c
                for c in buckets.get("commands", []) + assess
                if c.category == "vscode_regression"
            ]
        ),
        deferred_slice_inventory=DEFERRED,
        defects=all_defects,
        blockers=[],
        limitations=limitations,
        total_checks=len(all_checks),
        failed_checks=failed,
        checks=all_checks,
    )
    leaks = report_contains_forbidden_leak(str(report.to_dict()))
    if leaks:
        report.verdict = "FAIL"
        report.defects.append(
            Defect("harness defect", "report_safety", "no leaks", ",".join(leaks))
        )
        report.failed_checks += 1
        report.total_checks += 1
    return report


def write_verification_outputs(
    report: VsCodeCommunityWorkflowReport, monorepo: Path
) -> Path:
    out = monorepo / SV131_OUTPUT_RELATIVE
    out.mkdir(parents=True, exist_ok=True)
    path = out / REPORT_JSON
    report.write_json(path)
    (out / REPORT_MD).write_text(
        f"# {report.schema_name}:{report.schema_version}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        f"Operations: {', '.join(report.operation_inventory)}\n\n"
        "Epic 13 complete for v0.2.0 epic scope (see sv13-15). "
        "Epic 14 Product Experience not started. No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return path


def run(monorepo: Path | None = None) -> VsCodeCommunityWorkflowReport:
    root = monorepo or monorepo_root_from_here()
    report = build_report(root)
    write_verification_outputs(report, root)
    return report
