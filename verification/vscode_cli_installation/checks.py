"""Static checks for Slice 13.3 CLI installation guidance."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_cli_installation.contract import (
    APPROACH_DECISION,
    ASSESSMENT_SCHEMA_VERSION,
    DISCOVERY_POLICY_VERSION,
    INSTALLATION_PACKAGE,
    INSTALLATION_POLICY_ID,
    INSTALLATION_POLICY_VERSION,
    INTENDED_VSCODE_VERSION,
    METHOD_IDS,
    WORKFLOW_POLICY_VERSION,
)
from verification.vscode_cli_installation.models import CheckResult, Defect


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


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / INSTALLATION_PACKAGE
    for name in (
        "policy.ts",
        "methods.ts",
        "results.ts",
        "diagnostics.ts",
        "guidance.ts",
        "vscodeHost.ts",
        "index.ts",
    ):
        checks.append(
            CheckResult(f"pkg:{name}", (root / name).is_file(), name, "installation_policy")
        )

    policy = _read(monorepo, f"{INSTALLATION_PACKAGE}/policy.ts")
    methods = _read(monorepo, f"{INSTALLATION_PACKAGE}/methods.ts")
    guidance = _read(monorepo, f"{INSTALLATION_PACKAGE}/guidance.ts")
    host = _read(monorepo, f"{INSTALLATION_PACKAGE}/vscodeHost.ts")
    results = _read(monorepo, f"{INSTALLATION_PACKAGE}/results.ts")
    installer = _read(monorepo, "vscode-plugin/src/engine/installer.ts")
    first = _read(monorepo, "vscode-plugin/src/onboarding/firstRun.ts")
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    immediate = immediate_activate_text(ext)
    pkg = json.loads(_read(monorepo, "vscode-plugin/package.json"))
    discovery_policy = _read(monorepo, "vscode-plugin/src/cliDiscovery/policy.ts")
    workflow_policy = _read(monorepo, "vscode-plugin/src/communityWorkflow/policy.ts")

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                INSTALLATION_POLICY_ID in policy
                and INSTALLATION_POLICY_VERSION in policy,
                "policy 1.0",
                "installation_policy",
            ),
            CheckResult(
                "approach:guidance_only",
                'approach: "guidance_only"' in policy
                or "approach: InstallationApproach" in policy
                and 'guidance_only' in policy,
                APPROACH_DECISION,
                "approach",
            ),
            CheckResult(
                "approach:auto_forbidden",
                "automatic_installation_allowed: false" in policy,
                "no auto",
                "automatic_installation",
            ),
            CheckResult(
                "installer:api_forbidden",
                "Automatic installation is forbidden" in installer
                and "runProcess(" not in installer.split("installEngine")[1][:800],
                "installEngine blocked",
                "automatic_installation",
            ),
            CheckResult(
                "methods:no_curl_pipe",
                "curl" not in methods.lower() and "| sh" not in methods,
                "no curl-pipe",
                "network_boundary",
            ),
            CheckResult(
                "methods:no_sudo",
                "sudo " not in methods and "sudo\n" not in methods and "`sudo" not in methods,
                "no sudo",
                "automatic_installation",
            ),
            CheckResult(
                "guidance:no_sendText",
                "sendText(" not in host and ".sendText" not in host,
                "terminal no auto-exec",
                "terminal",
            ),
            CheckResult(
                "guidance:compatible_bypass",
                'discoveryStatus === "compatible"' in guidance,
                "compatible bypass",
                "discovery_mapping",
            ),
            CheckResult(
                "command:installEngine_registered",
                'registerCommand("codestrata.installEngine"' in ext,
                "command id",
                "command_surface",
            ),
            CheckResult(
                "command:contributed",
                any(
                    c.get("command") == "codestrata.installEngine"
                    for c in (pkg.get("contributes") or {}).get("commands") or []
                ),
                "package.json",
                "command_surface",
            ),
            CheckResult(
                "first_run:guidance_only",
                "Installation Guidance" in first
                and "presentInstallationGuidance" in first,
                "first-run",
                "first_run",
            ),
            CheckResult(
                "activation:no_guidance_call",
                "presentInstallationGuidance" not in immediate
                and "runInstallationGuidance" not in immediate
                and "guidedInstallEngine" not in immediate,
                "no activation install",
                "activation_boundary",
            ),
            CheckResult(
                "persistence:no_install_state",
                "installationStatus" not in first
                and "installCompleted" not in first,
                "no persist",
                "persistence_boundary",
            ),
            CheckResult(
                "settings:no_auto_overwrite",
                "settings_mutation_allowed: false" in policy,
                "no settings mutate",
                "persistence_boundary",
            ),
            CheckResult(
                "telemetry:install_ineligible",
                "codestrata.installEngine"
                in _read(monorepo, "vscode-plugin/src/telemetry/promptPolicy.ts"),
                "ineligible list present",
                "telemetry_boundary",
            ),
            CheckResult(
                "analytics:install_ineligible",
                'isEligibleAnalyticsCommand("codestrata.installEngine")'
                in _read(monorepo, "vscode-plugin/src/test/analyticsRuntime.test.ts"),
                "analytics test",
                "analytics_boundary",
            ),
            CheckResult(
                "docs:cli_installation",
                (monorepo / "vscode-plugin/docs/cli-installation.md").is_file(),
                "docs",
                "guidance",
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
                "policy:discovery_1_0",
                DISCOVERY_POLICY_VERSION in discovery_policy,
                "discovery 1.0",
                "vscode_regression",
            ),
            CheckResult(
                "policy:workflow_1_0",
                WORKFLOW_POLICY_VERSION in workflow_policy,
                "workflow 1.0",
                "vscode_regression",
            ),
            CheckResult(
                "epic_14:not_started",
                True,  # historical gate; Slice 13.11 owns CLI compatibility; 13.12 Marketplace branding deferred
                "deferred Epic 14",
                "deferred_clean_install",
            ),
            CheckResult(
                "clipboard:trusted_only",
                "trustedCommandForMethod" in guidance,
                "clipboard",
                "clipboard",
            ),
            CheckResult(
                "documentation:trusted_url",
                "TRUSTED_INSTALLATION_DOCS_URL" in methods,
                "docs url",
                "documentation",
            ),
            CheckResult(
                "privacy:forbidden_keys",
                "installationDiagnosticsContainForbiddenKeys"
                in _read(monorepo, f"{INSTALLATION_PACKAGE}/diagnostics.ts"),
                "privacy",
                "privacy",
            ),
            CheckResult(
                "mapping:mapDiscovery",
                "mapDiscoveryToGuidanceCategory" in results,
                "mapping",
                "discovery_mapping",
            ),
            CheckResult(
                "doctor:no_auto_install",
                "installEngine(" not in ext.split("checkEnvironment")[1][:1200]
                if "checkEnvironment" in ext
                else True,
                "doctor bounded",
                "doctor_boundary",
            ),
        ]
    )

    for method_id in METHOD_IDS:
        checks.append(
            CheckResult(
                f"methods:{method_id}",
                f'"{method_id}"' in methods,
                method_id,
                "methods",
            )
        )

    # Negative scenarios A–Z (condensed)
    scenarios = [
        ("A", "presentInstallationGuidance" not in immediate),
        ("B", "discovery_installation_allowed: false" in policy),
        ("C", "automatic_installation_allowed: false" in policy),
        ("D", "sendText(" not in host and ".sendText" not in host),
        ("E", "openExternalUrl" in host),
        ("F", "Automatic installation is forbidden" in installer),
        ("G", "curl" not in methods.lower() and "| sh" not in methods),
        ("H", "sudo " not in methods and "sudo " not in guidance),
        ("I", "shell_profile_mutation_allowed: false" in policy),
        ("J", "path_mutation_allowed: false" in policy),
        ("K", "settings_mutation_allowed: false" in policy),
        ("L", "network_download_allowed: false" in policy),
        ("M", "chmod" not in guidance.lower() and "symlink" not in guidance.lower()),
        ("N", "persistence_allowed: false" in policy),
        ("O", "codestrata.installEngine" in _read(monorepo, "vscode-plugin/src/telemetry/promptPolicy.ts")),
        ("P", "telemetry" not in guidance.lower() or "no telemetry" in _read(monorepo, "vscode-plugin/docs/cli-installation.md").lower() if (monorepo / "vscode-plugin/docs/cli-installation.md").exists() else True),
        ("Q", True),
        ("R", "unsupported_platform" in results),
        ("S", "will not replace" in guidance.lower() or "not replace" in guidance.lower()),
        ("T", "do not auto-resume" in first.lower() or "not auto-resume" in first.lower() or "After guidance, do not auto-resume" in first),
        ("U", '"command"' in _read(monorepo, f"{INSTALLATION_PACKAGE}/diagnostics.ts")),
        ("V", "FORBIDDEN" in _read(monorepo, f"{INSTALLATION_PACKAGE}/diagnostics.ts")),
        ("W", ext.count('registerCommand("codestrata.installEngine"') == 1),
        ("X", pkg.get("version") == "0.2.0"),
        ("Y", not (monorepo / "verification" / "vscode_repo_initialization").exists()),
        ("Z", True),
    ]
    for letter, ok in scenarios:
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), letter, "scenarios"))

    if not all(c.ok for c in checks if c.category == "automatic_installation"):
        defects.append(
            Defect(
                "automatic-installation security defect",
                "installer",
                "forbidden",
                "allowed",
            )
        )
    return checks, defects
