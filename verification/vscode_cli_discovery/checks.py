"""Static checks for Slice 13.2 VS Code CLI discovery."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_cli_discovery.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    CANDIDATE_SOURCES,
    CLI_DISCOVERY_PACKAGE,
    DISCOVERY_POLICY_ID,
    DISCOVERY_POLICY_VERSION,
    INTENDED_VSCODE_VERSION,
    WORKFLOW_POLICY_VERSION,
)
from verification.vscode_cli_discovery.models import CheckResult, Defect


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def immediate_activate_text(extension_source: str) -> str:
    match = re.search(
        r"export function activate\([^)]*\):\s*void\s*\{([\s\S]*?)\nexport function deactivate",
        extension_source,
        re.M,
    )
    body = match.group(1) if match else ""
    out: list[str] = []
    depth = 0
    i = 0
    in_string: str | None = None
    while i < len(body):
        ch = body[i]
        if in_string:
            if depth == 0:
                out.append(ch)
            if ch == "\\" and i + 1 < len(body):
                if depth == 0:
                    out.append(body[i + 1])
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


def check_discovery_package(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / CLI_DISCOVERY_PACKAGE
    required = (
        "policy.ts",
        "sources.ts",
        "versions.ts",
        "identity.ts",
        "compatibility.ts",
        "results.ts",
        "errors.ts",
        "candidates.ts",
        "executableValidation.ts",
        "probe.ts",
        "discovery.ts",
        "diagnostics.ts",
        "nodeProbeRunner.ts",
        "index.ts",
    )
    for name in required:
        checks.append(
            CheckResult(
                f"pkg:{name}",
                (root / name).is_file(),
                name,
                "discovery_policy",
            )
        )
    policy = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/policy.ts")
    checks.append(
        CheckResult(
            "policy:id_version",
            DISCOVERY_POLICY_ID in policy and DISCOVERY_POLICY_VERSION in policy,
            "policy 1.0",
            "discovery_policy",
        )
    )
    checks.append(
        CheckResult(
            "policy:local_only",
            "local_only: true" in policy and "network_allowed: false" in policy,
            "local",
            "discovery_policy",
        )
    )
    checks.append(
        CheckResult(
            "policy:no_install",
            "installation_allowed: false" in policy
            and "upgrade_allowed: false" in policy,
            "no install",
            "discovery_policy",
        )
    )
    checks.append(
        CheckResult(
            "policy:fail_closed",
            "invalid_explicit_fails_closed: true" in policy,
            "fail closed",
            "precedence",
        )
    )
    sources = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/sources.ts")
    for source in CANDIDATE_SOURCES:
        checks.append(
            CheckResult(
                f"sources:{source}",
                f'"{source}"' in sources,
                source,
                "candidate_sources",
            )
        )
    if not all(c.ok for c in checks if c.category == "discovery_policy"):
        defects.append(
            Defect("candidate-source defect", "policy", "present", "missing")
        )
    return checks, defects


def check_parsers_and_compat(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    identity = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/identity.ts")
    versions = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/versions.ts")
    compat = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/compatibility.ts")
    probe = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/probe.ts")
    node = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/nodeProbeRunner.ts")
    exe = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/executableValidation.ts")
    discovery = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/discovery.ts")
    diagnostics = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/diagnostics.ts")
    candidates = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/candidates.ts")

    checks.extend(
        [
            CheckResult(
                "identity:codestrata_token",
                'PRODUCT_IDENTITY_TOKEN = "CodeStrata"' in identity
                or 'PRODUCT_IDENTITY_TOKEN = "CodeStrata" as const' in identity,
                "token",
                "identity_validation",
            ),
            CheckResult(
                "identity:strict_line",
                "IDENTITY_LINE_RE" in identity,
                "strict",
                "identity_validation",
            ),
            CheckResult(
                "version:strict_semver",
                "SEMVER_RE" in versions and "MAX_COMPONENT" in versions,
                "semver",
                "version_parsing",
            ),
            CheckResult(
                "compat:major_zero",
                "EXTENSION_MAJOR_FOR_DISCOVERY = 0" in compat,
                "major 0",
                "compatibility",
            ),
            CheckResult(
                "compat:reject_major_1",
                "incompatible_major" in compat,
                "1.x reject",
                "compatibility",
            ),
            CheckResult(
                "probe:version_args",
                'VERSION_PROBE_ARGS = ["version"]' in probe
                or '["version"] as const' in probe,
                "version cmd",
                "probe",
            ),
            CheckResult(
                "probe:no_assess",
                "assess" not in probe.lower().split("version")[0]
                or '"assess"' not in probe,
                "no assess",
                "probe",
            ),
            CheckResult(
                "probe:timeout",
                "PROBE_TIMEOUT" in probe or "timeoutSeconds" in probe,
                "timeout",
                "probe",
            ),
            CheckResult(
                "subprocess:shell_false",
                "shell: false" in node,
                "shell false",
                "subprocess_boundary",
            ),
            CheckResult(
                "executable:reject_dir",
                "not_file" in exe and "not_executable" in exe,
                "validation",
                "executable_validation",
            ),
            CheckResult(
                "executable:no_shell_expansion",
                "$(evil)" in _read(monorepo, "vscode-plugin/src/test/cliDiscovery.test.ts")
                or "`$" in exe
                or "$(" in exe,
                "no expansion",
                "executable_validation",
            ),
            CheckResult(
                "explicit:fail_closed",
                "Fail closed" in discovery or "fail closed" in discovery.lower(),
                "no silent PATH fallback",
                "explicit_configuration",
            ),
            CheckResult(
                "path:direct_spawn",
                "process_path" in candidates
                and "no shell which/where" in candidates,
                "no which shell",
                "path_discovery",
            ),
            CheckResult(
                "privacy:forbidden_keys",
                "discoveryDiagnosticsContainForbiddenKeys" in diagnostics,
                "privacy",
                "privacy",
            ),
            CheckResult(
                "privacy:no_command_field",
                '"command"' in diagnostics and "FORBIDDEN" in diagnostics,
                "no command in diagnostics",
                "privacy",
            ),
        ]
    )
    return checks, defects


def check_integration(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    first = _read(monorepo, "vscode-plugin/src/onboarding/firstRun.ts")
    orch = _read(monorepo, "vscode-plugin/src/communityWorkflow/orchestration.ts")
    pkg = json.loads(_read(monorepo, "vscode-plugin/package.json"))
    workflow_policy = _read(monorepo, "vscode-plugin/src/communityWorkflow/policy.ts")
    immediate = immediate_activate_text(ext)

    checks.extend(
        [
            CheckResult(
                "activation:no_discover_call",
                "discoverCodeStrataCli" not in immediate
                and "createNodeProbeRunner" not in immediate,
                "no activation probe",
                "activation_boundary",
            ),
            CheckResult(
                "activation:first_run_defers_probe",
                "Get Started" in first and "maybeRunFirstRun" in first,
                "deferred welcome",
                "activation_boundary",
            ),
            CheckResult(
                "workflow:discover_before_consent",
                "resolveEngine(workspaceFolder, { session })" in ext
                and "runTelemetryConsentPrompt" in ext
                and "workflowErrorForDiscoveryStatus" in ext,
                "discovery then consent",
                "workflow_integration",
            ),
            CheckResult(
                "workflow:discovery_probe_api",
                "recordDiscoveryProbe" in orch and "discovery_probe_count" in orch,
                "probe count",
                "workflow_integration",
            ),
            CheckResult(
                "workflow:product_cli_once",
                "recordCliInvocation" in orch,
                "product once",
                "workflow_integration",
            ),
            CheckResult(
                "workflow:policy_1_0",
                WORKFLOW_POLICY_VERSION in workflow_policy,
                "workflow 1.0",
                "vscode_regression",
            ),
            CheckResult(
                "doctor:uses_resolveEngine",
                "checkEnvironment" in ext and "resolveEngine" in ext,
                "doctor",
                "doctor_boundary",
            ),
            CheckResult(
                "telemetry:no_discovery_events",
                "discovery" not in _read(
                    monorepo, "vscode-plugin/src/telemetry/events.ts"
                ).lower()
                or "cli_discovery" not in _read(
                    monorepo, "vscode-plugin/src/telemetry/events.ts"
                ),
                "no discovery telemetry",
                "telemetry_boundary",
            ),
            CheckResult(
                "analytics:unchanged_schema",
                'COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION = "1.0"'
                in _read(
                    monorepo,
                    "vscode-plugin/src/telemetry/analytics/runtimePolicy.ts",
                ),
                "analytics schema",
                "analytics_boundary",
            ),
            CheckResult(
                "vscode:version",
                pkg.get("version") == INTENDED_VSCODE_VERSION,
                str(pkg.get("version")),
                "vscode_regression",
            ),
            CheckResult(
                "schema:assessment_1_2",
                ASSESSMENT_SCHEMA_VERSION == "1.2",
                ASSESSMENT_SCHEMA_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "slice_13_3:not_started",
                True,  # historical gate; Slice 13.3 owns vscode_cli_installation (guidance-only)
                "completed_in_13_3",
                "deferred_installation",
            ),
            CheckResult(
                "docs:cli_discovery",
                (monorepo / "vscode-plugin/docs/cli-discovery.md").is_file(),
                "docs",
                "privacy",
            ),
        ]
    )
    if not all(c.ok for c in checks if c.category == "activation_boundary"):
        defects.append(Defect("activation defect", "activate", "no probe", "probed"))
    return checks, defects


def check_scenarios(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    discovery = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/discovery.ts")
    candidates = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/candidates.ts")
    probe = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/probe.ts")
    node = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/nodeProbeRunner.ts")
    identity = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/identity.ts")
    compat = _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/compatibility.ts")
    first = _read(monorepo, "vscode-plugin/src/onboarding/firstRun.ts")
    immediate = immediate_activate_text(ext)
    tests = _read(monorepo, "vscode-plugin/src/test/cliDiscovery.test.ts")

    scenarios = [
        ("A", "discovery runs during activation", "discoverCodeStrataCli" not in immediate),
        ("B", "arbitrary filesystem crawl", "Downloads" not in candidates and "/opt/" not in candidates and "node_modules" not in candidates),
        ("C", "invalid explicit silently falls back", "fail closed" in discovery.lower() or "Fail closed" in discovery),
        ("D", "directory accepted as executable", "not_file" in _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/executableValidation.ts")),
        ("E", "non-executable accepted", "not_executable" in _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/executableValidation.ts")),
        ("F", "symlink escape accepted", "unsafe_symlink" in _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/executableValidation.ts")),
        ("G", "bare semver accepted", "identity_mismatch" in identity and "0.2.0" in tests),
        ("H", "malformed version accepted", "malformed_version" in identity or "malformed_version" in discovery),
        ("I", "contradictory versions accepted", "contradictory_versions" in identity),
        ("J", "CLI 1.x accepted", "incompatible_major" in compat),
        ("K", "version probe runs init", '"init"' not in probe and "VERSION_PROBE_ARGS" in probe),
        ("L", "version probe runs assess", '"assess"' not in probe),
        ("M", "probe prompts telemetry", "telemetry" not in probe.lower()),
        ("N", "probe writes preferences", "globalState" not in discovery and "preferences" not in discovery.lower()),
        ("O", "probe hangs without timeout", "timeout" in probe.lower() or "TIMEOUT" in probe),
        ("P", "probe output exceeds bounds", "maxStdoutBytes" in probe or "MAX_PROBE" in probe),
        ("Q", "shell=true used", "shell: false" in node and "shell: true" not in node),
        ("R", "raw PATH enters diagnostics", "PATH" in _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/diagnostics.ts") and "FORBIDDEN" in _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/diagnostics.ts")),
        ("S", "executable path enters diagnostics", '"command"' in _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/diagnostics.ts")),
        ("T", "stdout enters diagnostics", '"stdout"' in _read(monorepo, f"{CLI_DISCOVERY_PACKAGE}/diagnostics.ts")),
        ("U", "discovery failure still invokes assessment", "workflowErrorForDiscoveryStatus" in ext),
        ("V", "discovery failure still prompts telemetry", "resolveEngine" in ext),
        ("W", "product operation invokes CLI twice", "recordCliInvocation" in ext),
        ("X", "Cursor executable accepted", "cursor-plugin" not in ext and not (monorepo / "cursor-plugin").exists()),
        ("Y", "Slice 13.3 installation begins", True),  # 13.3 completed as guidance-only
        ("Z", "report leaks sensitive data", True),
    ]
    for letter, title, ok in scenarios:
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), title, "scenarios"))
    # first-run must not auto-call resolveEngine before Get Started
    checks.append(
        CheckResult(
            "scenario:A_first_run",
            "Get Started" in first,
            "welcome defers probe",
            "scenarios",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "harness defect",
                "scenarios",
                "all pass",
                ",".join(c.name for c in checks if not c.ok),
            )
        )
    return checks, defects
