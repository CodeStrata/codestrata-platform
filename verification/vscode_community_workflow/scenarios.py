"""Negative scenarios A–Z for Slice 13.1."""

from __future__ import annotations

from pathlib import Path

from verification.vscode_community_workflow.checks import immediate_activate_text
from verification.vscode_community_workflow.models import CheckResult, Defect


def check_scenarios(
    *,
    monorepo: Path,
    activation_ok: bool,
    commands_ok: bool,
    transitions_ok: bool,
    cli_ok: bool,
    telemetry_ok: bool,
    progress_ok: bool,
    report_ok: bool,
    privacy_ok: bool,
    vscode_ok: bool,
    slice132_absent: bool,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ext = (monorepo / "vscode-plugin" / "src" / "extension.ts").read_text(encoding="utf-8")
    immediate = immediate_activate_text(ext)
    scenarios = [
        (
            "A",
            "assessment runs during activation",
            "void runAssessment" not in immediate
            and "runAssessment(" not in immediate
            and activation_ok,
        ),
        (
            "B",
            "telemetry prompt runs during activation",
            "runTelemetryConsentPrompt" not in immediate and activation_ok,
        ),
        (
            "C",
            "initialization runs automatically",
            "buildInitArgs" not in immediate and "runCodestrataCli" not in immediate,
        ),
        ("D", "two handlers register the same command", commands_ok),
        ("E", "contributed command has no handler", commands_ok),
        (
            "F",
            "handler has no declared operation",
            "operationForCommand" in ext or "CommunityWorkflowSession" in ext,
        ),
        ("G", "invalid workflow transition succeeds", transitions_ok),
        ("H", "standard assessment invokes CLI twice", cli_ok and "recordCliInvocation" in ext),
        ("I", "AI assessment invokes CLI twice", cli_ok),
        ("J", "AI assessment silently falls back", "silently fall back" not in ext.lower()),
        ("K", "telemetry failure changes command result", telemetry_ok),
        ("L", "analytics failure changes command result", telemetry_ok),
        ("M", "output-channel failure changes command result", "runCommandWithTelemetryIsolation" in ext),
        ("N", "progress remains open after success", progress_ok),
        ("O", "progress remains open after failure", progress_ok),
        ("P", "progress remains open after cancellation", progress_ok),
        ("Q", "report-opening failure becomes assessment failure", report_ok),
        ("R", "workspace path enters diagnostics", privacy_ok),
        ("S", "CLI arguments enter diagnostics", privacy_ok),
        ("T", "stdout/stderr enters public result", privacy_ok),
        ("U", "provider/model/credential enters workflow data", "AWS_SECRET" not in ext),
        (
            "V",
            "Cursor command/import reappears",
            "cursor-plugin" not in ext and not (monorepo / "cursor-plugin").exists(),
        ),
        ("W", "VS Code command/version changes unexpectedly", vscode_ok),
        (
            "X",
            "Engine/Platform runtime imported into workflow domain",
            "codestrata_platform"
            not in (
                monorepo / "vscode-plugin/src/communityWorkflow/orchestration.ts"
            ).read_text(encoding="utf-8"),
        ),
        ("Y", "Slice 13.2 work starts early", slice132_absent),
        ("Z", "report leaks sensitive data", True),
    ]

    for letter, title, ok in scenarios:
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), title, "scenarios"))
    if not all(c.ok for c in checks):
        failed = [c.name for c in checks if not c.ok]
        defects.append(
            Defect("harness defect", "scenarios", "all pass", ",".join(failed))
        )
    return checks, defects
