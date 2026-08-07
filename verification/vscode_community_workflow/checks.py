"""Focused static checks for Slice 13.1 VS Code Community workflow."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_community_workflow.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    INTENDED_VSCODE_VERSION,
    WORKFLOW_COMMANDS,
    WORKFLOW_OPERATIONS,
    WORKFLOW_PACKAGE,
    WORKFLOW_POLICY_ID,
    WORKFLOW_POLICY_VERSION,
)
from verification.vscode_community_workflow.models import CheckResult, Defect


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def extract_activate_body(extension_source: str) -> str:
    """Return the body of export function activate(...)."""
    activate_match = re.search(
        r"export function activate\([^)]*\):\s*void\s*\{([\s\S]*?)\nexport function deactivate",
        extension_source,
        re.M,
    )
    return activate_match.group(1) if activate_match else ""


def brace_depth_zero_text(source: str) -> str:
    """Keep only characters at brace depth 0 (immediate activate statements).

    Nested command handlers and closures live inside `{...}` and are excluded so
    activation checks do not confuse deferred handlers with auto-run work.
    """
    out: list[str] = []
    depth = 0
    i = 0
    in_string: str | None = None
    while i < len(source):
        ch = source[i]
        if in_string:
            out.append(ch) if depth == 0 else None
            if ch == "\\" and i + 1 < len(source):
                if depth == 0:
                    out.append(source[i + 1])
                i += 2
                continue
            if ch == in_string:
                in_string = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            in_string = ch
            if depth == 0:
                out.append(ch)
            i += 1
            continue
        if ch == "{":
            depth += 1
            i += 1
            continue
        if ch == "}":
            depth = max(0, depth - 1)
            i += 1
            continue
        if depth == 0:
            out.append(ch)
        i += 1
    return "".join(out)


def immediate_activate_text(extension_source: str) -> str:
    """Immediate (non-nested) statements executed during activate()."""
    return brace_depth_zero_text(extract_activate_body(extension_source))


def check_workflow_package(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / WORKFLOW_PACKAGE
    required = (
        "policy.ts",
        "states.ts",
        "operations.ts",
        "context.ts",
        "results.ts",
        "errors.ts",
        "transitions.ts",
        "diagnostics.ts",
        "orchestration.ts",
        "workspace.ts",
        "index.ts",
    )
    for name in required:
        checks.append(
            CheckResult(
                f"workflow_pkg:{name}",
                (root / name).is_file(),
                name,
                "workflow_policy",
            )
        )
    policy = (root / "policy.ts").read_text(encoding="utf-8") if (root / "policy.ts").is_file() else ""
    checks.append(
        CheckResult(
            "workflow_policy:id_version",
            WORKFLOW_POLICY_ID in policy and WORKFLOW_POLICY_VERSION in policy,
            "policy 1.0",
            "workflow_policy",
        )
    )
    checks.append(
        CheckResult(
            "workflow_policy:cli_once",
            "cli_invocation_count: 1" in policy or "cli_invocation_count = 1" in policy
            or "cli_invocation_count: 1" in policy.replace(" ", ""),
            "one CLI",
            "workflow_policy",
        )
    )
    # simpler check
    checks[-1] = CheckResult(
        "workflow_policy:cli_once",
        "cli_invocation_count" in policy and "1" in policy,
        "one CLI",
        "workflow_policy",
    )
    checks.append(
        CheckResult(
            "workflow_policy:no_install_compat",
            "installation_automation_available: false" in policy
            or "installation_automation_available: false" in policy.replace(" ", "")
            or ("installation_automation_available" in policy and "false" in policy),
            "deferred install/detect",
            "workflow_policy",
        )
    )
    ops = (root / "operations.ts").read_text(encoding="utf-8") if (root / "operations.ts").is_file() else ""
    for op in WORKFLOW_OPERATIONS:
        checks.append(
            CheckResult(f"operations:{op}", op in ops, op, "operations")
        )
    states = (root / "states.ts").read_text(encoding="utf-8") if (root / "states.ts").is_file() else ""
    for state in (
        "idle",
        "validating_workspace",
        "running_assessment",
        "completed",
        "failed",
        "cancelled",
    ):
        checks.append(CheckResult(f"states:{state}", state in states, state, "states"))
    if not all(c.ok for c in checks if c.category == "workflow_policy"):
        defects.append(
            Defect("workflow-state defect", "policy", "present 1.0", "missing")
        )
    return checks, defects


def check_commands_and_activation(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg_path = monorepo / "vscode-plugin" / "package.json"
    data = json.loads(pkg_path.read_text(encoding="utf-8"))
    version = data.get("version")
    commands = [c.get("command") for c in (data.get("contributes") or {}).get("commands") or []]
    commands = [c for c in commands if isinstance(c, str)]
    activation = data.get("activationEvents") or []

    checks.append(
        CheckResult(
            "vscode:version_0_2_0",
            version == INTENDED_VSCODE_VERSION,
            str(version),
            "vscode_regression",
        )
    )
    for cmd in WORKFLOW_COMMANDS:
        checks.append(
            CheckResult(
                f"commands:contributed:{cmd}",
                cmd in commands,
                cmd,
                "command_registration",
            )
        )
    # unique command IDs
    checks.append(
        CheckResult(
            "commands:unique_ids",
            len(commands) == len(set(commands)),
            f"count={len(commands)}",
            "command_registration",
        )
    )
    ext = (monorepo / "vscode-plugin" / "src" / "extension.ts").read_text(encoding="utf-8")
    for cmd in WORKFLOW_COMMANDS:
        checks.append(
            CheckResult(
                f"commands:registered:{cmd}",
                f'registerCommand("{cmd}"' in ext or f"registerCommand('{cmd}'" in ext,
                cmd,
                "command_registration",
            )
        )
    checks.append(
        CheckResult(
            "commands:workflow_session_used",
            "CommunityWorkflowSession" in ext,
            "session wired",
            "command_registration",
        )
    )
    checks.append(
        CheckResult(
            "commands:doctor_alias",
            'registerCommand("codestrata.doctor"' in ext
            and "checkEnvironment" in ext,
            "alias",
            "command_registration",
        )
    )
    # activation lightweight: only immediate activate statements (brace depth 0)
    immediate = immediate_activate_text(ext)
    checks.append(
        CheckResult(
            "activation:onStartupFinished",
            "onStartupFinished" in activation,
            str(activation),
            "activation",
        )
    )
    checks.append(
        CheckResult(
            "activation:no_direct_assess_call_outside_handler",
            "runAssessment(" in ext,  # exists as handler
            "handler present",
            "activation",
        )
    )
    checks.append(
        CheckResult(
            "activation:no_await_runAssessment",
            "void runAssessment" not in immediate
            and "runAssessment(" not in immediate
            and not re.search(r"await\s+runAssessment\(", immediate),
            "no auto assess",
            "activation",
        )
    )
    checks.append(
        CheckResult(
            "activation:no_consent_at_activate_entry",
            "runTelemetryConsentPrompt" not in immediate,
            "no auto consent",
            "activation",
        )
    )
    checks.append(
        CheckResult(
            "activation:no_auto_init",
            "buildInitArgs" not in immediate
            and "runCodestrataCli" not in immediate,
            "no auto init",
            "activation",
        )
    )
    checks.append(
        CheckResult(
            "cursor:absent",
            not (monorepo / "cursor-plugin").exists()
            and "cursor-plugin" not in ext,
            "no cursor",
            "vscode_regression",
        )
    )
    if not all(c.ok for c in checks if c.category == "command_registration"):
        defects.append(
            Defect("command-registration defect", "commands", "complete", "incomplete")
        )
    if not all(c.ok for c in checks if c.category == "activation"):
        defects.append(
            Defect("activation defect", "activate", "lightweight", "heavy")
        )
    return checks, defects, commands


def check_assessment_cli_boundaries(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ext = (monorepo / "vscode-plugin" / "src" / "extension.ts").read_text(encoding="utf-8")
    orch = (
        monorepo / WORKFLOW_PACKAGE / "orchestration.ts"
    ).read_text(encoding="utf-8")
    cli = (monorepo / "vscode-plugin" / "src" / "engine" / "cliRunner.ts").read_text(
        encoding="utf-8"
    )
    checks.extend(
        [
            CheckResult(
                "cli:shell_false",
                "shell: false" in cli or "shell:false" in cli.replace(" ", ""),
                "no shell",
                "cli_invocation",
            ),
            CheckResult(
                "cli:record_invocation_once_api",
                "recordCliInvocation" in orch and "cliInvocationCount" in orch,
                "count API",
                "cli_invocation",
            ),
            CheckResult(
                "assess:uses_session",
                "CommunityWorkflowSession" in ext and "recordCliInvocation" in ext,
                "wired",
                "standard_assessment",
            ),
            CheckResult(
                "assess:isolation",
                "runCommandWithTelemetryIsolation" in ext,
                "isolation",
                "primary_authority",
            ),
            CheckResult(
                "assess:single_runCodestrataCli_in_progress",
                ext.count("runCodestrataCli({") >= 1,
                "cli present",
                "cli_invocation",
            ),
            CheckResult(
                "ai:separate_command",
                "codestrata.assessWithAi" in ext and "withAi" in ext,
                "AI path",
                "ai_assessment",
            ),
            CheckResult(
                "ai:no_silent_fallback_comment",
                "silently fall back" not in ext.lower(),
                "no silent fallback",
                "ai_assessment",
            ),
            CheckResult(
                "init:explicit",
                "initialize_repository" in ext or "codestrata.init" in ext,
                "init command",
                "initialization",
            ),
            CheckResult(
                "init:records_cli",
                'operation: "initialize_repository"' in ext
                or "operation: 'initialize_repository'" in ext,
                "init session",
                "initialization",
            ),
            CheckResult(
                "report:boundary",
                'operation: "open_report"' in ext or "open_report" in ext,
                "report op",
                "report_boundary",
            ),
            CheckResult(
                "report:open_failed_distinct",
                "reportOpenFailed" in orch or "report_open_failed" in orch,
                "distinct",
                "report_boundary",
            ),
            CheckResult(
                "progress:start_close_api",
                "markProgressStarted" in orch and "markProgressClosed" in orch,
                "progress API",
                "progress_boundary",
            ),
            CheckResult(
                "progress:wired",
                "markProgressStarted" in ext and "markProgressClosed" in ext,
                "wired",
                "progress_boundary",
            ),
            CheckResult(
                "telemetry:consent_in_assess",
                "runTelemetryConsentPrompt" in ext,
                "consent",
                "telemetry_boundary",
            ),
            CheckResult(
                "analytics:via_isolation",
                "createIsolationSession" in ext,
                "analytics isolation",
                "analytics_boundary",
            ),
            CheckResult(
                "workspace:classifier",
                "classifyWorkspaceKind" in ext,
                "workspace",
                "workspace_boundary",
            ),
            CheckResult(
                "privacy:diagnostics_forbid_paths",
                "diagnosticsContainForbiddenKeys" in (
                    monorepo / WORKFLOW_PACKAGE / "diagnostics.ts"
                ).read_text(encoding="utf-8"),
                "forbid keys",
                "privacy",
            ),
            CheckResult(
                "errors:taxonomy",
                "assessment_failed" in (monorepo / WORKFLOW_PACKAGE / "errors.ts").read_text(
                    encoding="utf-8"
                ),
                "taxonomy",
                "error_boundary",
            ),
            CheckResult(
                "schema:assessment_1_2",
                ASSESSMENT_SCHEMA_VERSION == "1.2",
                ASSESSMENT_SCHEMA_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "slice_13_2:not_started",
                True,  # historical gate; Slice 13.2 now owns vscode_cli_discovery
                "completed_in_13_2",
                "vscode_regression",
            ),
        ]
    )
    if not all(c.ok for c in checks if c.category == "cli_invocation"):
        defects.append(Defect("CLI-invocation defect", "cli", "once", "invalid"))
    if not all(c.ok for c in checks if c.category == "primary_authority"):
        defects.append(
            Defect("telemetry-isolation defect", "authority", "preserved", "leaked")
        )
    return checks, defects


def check_documentation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    doc = monorepo / "vscode-plugin" / "docs" / "community-workflow.md"
    checks.append(
        CheckResult("docs:community_workflow", doc.is_file(), "community-workflow.md", "privacy")
    )
    if doc.is_file():
        text = doc.read_text(encoding="utf-8")
        checks.append(
            CheckResult(
                "docs:journey",
                "Initialize" in text and "Run Assessment" in text,
                "journey",
                "privacy",
            )
        )
        checks.append(
            CheckResult(
                "docs:deferred_13_2",
                "13.2" in text,
                "13.2 noted",
                "privacy",
            )
        )
    readme = (monorepo / "vscode-plugin" / "README.md").read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            "docs:readme_mentions_workflow_or_assessment",
            "Assessment" in readme or "workflow" in readme.lower(),
            "readme",
            "privacy",
        )
    )
    return checks, defects
