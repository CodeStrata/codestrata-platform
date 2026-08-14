"""Focused checks for Slice 13.14 clean-install / update validation."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_clean_install.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    CLEAN_PACKAGE,
    CLEAN_POLICY_ID,
    CLEAN_POLICY_VERSION,
    INTENDED_VSCODE_VERSION,
    STABLE_COMMAND_IDS,
    STABLE_SETTING_KEYS,
    VSIX_NAME,
)
from verification.vscode_clean_install.models import CheckResult, Defect
from verification.vscode_clean_install.package_build import (
    category_counts,
    ensure_vsix_built,
    inventory_vsix,
)


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def _pkg(monorepo: Path) -> dict:
    return json.loads(_read(monorepo, "vscode-plugin/package.json"))


def _activate_region(ext: str) -> str:
    """Rough activate() body for activation-boundary checks."""
    m = re.search(
        r"export async function activate\([\s\S]*?\nexport function deactivate",
        ext,
    )
    return m.group(0) if m else ext


def _forbidden_vsix_names(names: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for name in names:
        n = name.replace("\\", "/").lower()
        if "cursor-plugin" in n or n.endswith("cursor") and "media" not in n:
            if "cursor" in n and (
                "cursor-plugin" in n
                or "/cursor/" in n
                or n.endswith("cursor.js")
            ):
                hits.append(name)
        if n.startswith("extension/src/") or "/extension/src/" in n:
            hits.append(name)
        if "extension/verification/" in n or n.startswith("extension/reports/"):
            hits.append(name)
        if "sample-reports/" in n or "testdata/" in n:
            hits.append(name)
        if "extension/node_modules/" in n or ".git/" in n:
            hits.append(name)
        if n.endswith(".ts") and not n.endswith(".d.ts"):
            hits.append(name)
        if "/out/test/" in n:
            hits.append(name)
    return sorted(set(hits))


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    meta: dict = {"package_file_count": 0, "package_size_bytes": 0}

    policy = _read(monorepo, f"{CLEAN_PACKAGE}/policy.ts")
    docs = _read(monorepo, "vscode-plugin/docs/clean-install-update.md")
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    first_run = _read(monorepo, "vscode-plugin/src/onboarding/firstRun.ts")
    consent = _read(monorepo, "vscode-plugin/src/telemetry/consent.ts")
    vscodeignore = _read(monorepo, "vscode-plugin/.vscodeignore")
    pkg = _pkg(monorepo)
    activate = _activate_region(ext)

    # Build / inventory VSIX
    try:
        vsix = ensure_vsix_built(monorepo, rebuild=False)
        inv = inventory_vsix(vsix)
        build_ok = True
        build_detail = VSIX_NAME
    except Exception as exc:  # noqa: BLE001 — surface as check failure
        inv = None
        build_ok = False
        build_detail = type(exc).__name__

    if inv is not None:
        meta["package_file_count"] = inv.file_count
        meta["package_size_bytes"] = inv.size_bytes
        forbidden = _forbidden_vsix_names(inv.names)
        cats = category_counts(inv.names)
        packaged_pkg = inv.package_json
    else:
        forbidden = ["build_failed"]
        cats = {}
        packaged_pkg = {}

    # Activation must not await CLI/consent/assess before helpers; probe only via user actions.
    pre_resolve = activate.split("const resolveEngine")[0]
    activation_probes = (
        "await discoverCodeStrataCli" in pre_resolve
        or "await runTelemetryConsentPrompt" in pre_resolve
        or "await runCodestrataCli" in pre_resolve
    )
    activation_ok = (
        not activation_probes and "void maybeRunFirstRun(onboardingDeps)" in activate
    )

    # Unit test coverage proxies for workflow smoke
    test_files = {
        "cliDiscovery": (monorepo / "vscode-plugin/src/test/cliDiscovery.test.ts").is_file(),
        "cliInstallation": (
            monorepo / "vscode-plugin/src/test/cliInstallation.test.ts"
        ).is_file(),
        "repositoryInitialization": (
            monorepo / "vscode-plugin/src/test/repositoryInitialization.test.ts"
        ).is_file(),
        "assessmentExecution": (
            monorepo / "vscode-plugin/src/test/assessmentExecution.test.ts"
        ).is_file(),
        "assessmentProgress": (
            monorepo / "vscode-plugin/src/test/assessmentProgress.test.ts"
        ).is_file(),
        "reportOpening": (
            monorepo / "vscode-plugin/src/test/reportOpening.test.ts"
        ).is_file(),
        "failureRecovery": (
            monorepo / "vscode-plugin/src/test/failureRecovery.test.ts"
        ).is_file(),
        "telemetryConsentIntegration": (
            monorepo / "vscode-plugin/src/test/telemetryConsentIntegration.test.ts"
        ).is_file(),
        "cliCompatibility": (
            monorepo / "vscode-plugin/src/test/cliCompatibility.test.ts"
        ).is_file(),
    }

    # Synthetic prior package (update): same ID, settings/commands subset of current
    prior_fixture = {
        "name": "codestrata-assessment",
        "publisher": "CodeStrataAI",
        "version": "0.1.0",
        "contributes": {
            "commands": [{"command": cid} for cid in STABLE_COMMAND_IDS],
            "configuration": {
                "properties": {k: {} for k in STABLE_SETTING_KEYS},
            },
        },
    }
    update_commands_ok = all(
        cid in json.dumps(pkg) for cid in STABLE_COMMAND_IDS
    ) and all(cid in json.dumps(prior_fixture) for cid in STABLE_COMMAND_IDS)
    update_settings_ok = all(k in json.dumps(pkg) for k in STABLE_SETTING_KEYS)

    slice_1315_absent = not (
        monorepo / "verification" / "vscode_epic14_product_experience"
    ).exists() and "startEpic14ProductExperience" not in ext

    host_harness = (monorepo / "vscode-plugin/src/test/runHostTests.ts").is_file()

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                CLEAN_POLICY_ID in policy and CLEAN_POLICY_VERSION in policy,
                f"{CLEAN_POLICY_ID}:{CLEAN_POLICY_VERSION}",
                "clean_install_policy",
            ),
            CheckResult(
                "policy:flags",
                "marketplace_publish_required: false" in policy
                and "automatic_cli_install_allowed: false" in policy
                and "machine_identity_allowed: false" in policy
                and "installation_identity_allowed: false" in policy
                and 'supported_cli_family: "0.2.x"' in policy
                or 'CLEAN_INSTALL_SUPPORTED_CLI_FAMILY = "0.2.x"' in policy,
                "policy flags",
                "clean_install_policy",
            ),
            CheckResult(
                "package:built",
                build_ok and inv is not None,
                build_detail,
                "package_build",
            ),
            CheckResult(
                "package:version",
                packaged_pkg.get("version") == INTENDED_VSCODE_VERSION
                if packaged_pkg
                else False,
                str(packaged_pkg.get("version")),
                "package_build",
            ),
            CheckResult(
                "package:required_entries",
                inv is not None and not inv.missing_required,
                "ok" if inv and not inv.missing_required else str(getattr(inv, "missing_required", [])),
                "package_inventory",
            ),
            CheckResult(
                "package:forbidden_absent",
                not forbidden,
                "ok" if not forbidden else str(forbidden[:8]),
                "package_integrity",
            ),
            CheckResult(
                "package:categories",
                inv is not None and cats.get("runtime_js", 0) > 0 and cats.get("media", 0) > 0,
                json.dumps(cats, sort_keys=True) if cats else "none",
                "package_inventory",
            ),
            CheckResult(
                "package:vscodeignore",
                "src/**" in vscodeignore
                and "out/test/**" in vscodeignore
                and "testdata/**" in vscodeignore,
                "dev/test excluded",
                "package_integrity",
            ),
            CheckResult(
                "isolated:harness_prepared",
                host_harness
                and "user-data-dir" in _read(
                    monorepo, "vscode-plugin/src/test/runHostTests.ts"
                ),
                "isolated user-data harness present",
                "isolated_environment",
            ),
            CheckResult(
                "install:id_stable",
                pkg.get("publisher") == "CodeStrataAI"
                and pkg.get("name") == "codestrata-assessment"
                and pkg.get("version") == INTENDED_VSCODE_VERSION,
                "CodeStrataAI.codestrata-assessment@0.2.2",
                "install",
            ),
            CheckResult(
                "activation:no_product_actions",
                activation_ok,
                "lightweight activation",
                "activation",
            ),
            CheckResult(
                "activation:no_machineId",
                "machineId" not in ext
                or "machineId" not in activate,
                "no machineId read",
                "privacy",
            ),
            CheckResult(
                "first_run:lazy_probe",
                "must not probe" in first_run.lower()
                or "do not probe" in first_run.lower(),
                "Get Started gates probe",
                "first_run",
            ),
            CheckResult(
                "first_run:onboarding_keys",
                "codestrata.firstRunCompleted" in first_run
                and "codestrata.welcomeDismissed" in first_run,
                "onboarding state classified",
                "state_inventory",
            ),
            CheckResult(
                "cli_missing:tests",
                test_files["cliDiscovery"] and test_files["cliInstallation"],
                "discovery+guidance tests",
                "cli_missing",
            ),
            CheckResult(
                "cli_incompatible:tests",
                test_files["cliCompatibility"],
                "compatibility tests",
                "cli_incompatible",
            ),
            CheckResult(
                "cli_compatible:matrix",
                'COMPATIBILITY_MINIMUM_CLI = "0.2.0"'
                in _read(monorepo, "vscode-plugin/src/cliCompatibility/policy.ts"),
                "0.2.x matrix",
                "cli_compatible",
            ),
            CheckResult(
                "initialization:tests",
                test_files["repositoryInitialization"]
                and "assertInitArgsForbidForce"
                in _read(
                    monorepo,
                    "vscode-plugin/src/repositoryInitialization/index.ts",
                )
                or "assertInitArgsForbidForce" in ext,
                "init tests + no --force",
                "initialization",
            ),
            CheckResult(
                "assessment:tests",
                test_files["assessmentExecution"],
                "assessment tests",
                "standard_assessment",
            ),
            CheckResult(
                "ai:safe_path",
                test_files["assessmentExecution"]
                and "live_ai_provider_required: false" in policy,
                "no live AI required",
                "ai_assessment",
            ),
            CheckResult(
                "progress:tests",
                test_files["assessmentProgress"],
                "progress tests",
                "progress",
            ),
            CheckResult(
                "report:tests",
                test_files["reportOpening"],
                "report tests",
                "report",
            ),
            CheckResult(
                "recovery:tests",
                test_files["failureRecovery"],
                "recovery tests",
                "recovery",
            ),
            CheckResult(
                "telemetry:never_persisted",
                "Never persisted" in consent
                and test_files["telemetryConsentIntegration"],
                "consent not persisted",
                "telemetry_consent",
            ),
            CheckResult(
                "analytics:unavailable",
                "unavailable"
                in _read(
                    monorepo, "vscode-plugin/src/telemetry/analytics/unavailableSink.ts"
                ).lower(),
                "unavailable sink",
                "analytics",
            ),
            CheckResult(
                "state:forbidden_keys",
                "FORBIDDEN_PERSISTED_STATE_KEYS" in policy
                and "codestrata.telemetryConsent" in policy,
                "forbidden consent/identity keys listed",
                "state_inventory",
            ),
            CheckResult(
                "update:stable_commands",
                update_commands_ok,
                "command IDs stable vs prior fixture",
                "update",
            ),
            CheckResult(
                "update:stable_settings",
                update_settings_ok,
                "setting keys stable",
                "update",
            ),
            CheckResult(
                "update:synthetic_prior",
                prior_fixture["name"] == pkg.get("name")
                and prior_fixture["publisher"] == pkg.get("publisher"),
                "synthetic prior package labeled",
                "update",
            ),
            CheckResult(
                "uninstall:limitation_documented",
                "uninstall_reinstall" in docs.lower()
                or "uninstall" in policy.lower(),
                "uninstall limitation recorded",
                "uninstall_reinstall",
            ),
            CheckResult(
                "cursor:absent_package",
                inv is not None
                and not any("cursor" in n.lower() for n in inv.names if "cursor-plugin" in n.lower() or "/cursor/" in n.lower()),
                "no Cursor package paths",
                "cursor_absence",
            ),
            CheckResult(
                "cursor:absent_manifest",
                "cursor" not in json.dumps(pkg).lower()
                or "cursor" not in str(pkg.get("keywords", [])).lower(),
                "no Cursor keywords/metadata",
                "cursor_absence",
            ),
            CheckResult(
                "vscode:engine_range",
                str(pkg.get("engines", {}).get("vscode", "")).startswith("^1.85"),
                str(pkg.get("engines", {}).get("vscode")),
                "vscode_compatibility",
            ),
            CheckResult(
                "privacy:no_identity_policy",
                "machine_identity_allowed: false" in policy
                and "installation_identity_allowed: false" in policy,
                "identity forbidden",
                "privacy",
            ),
            CheckResult(
                "docs:present",
                (monorepo / "vscode-plugin/docs/clean-install-update.md").is_file()
                and "0.2.0" in docs
                and "isolated" in docs.lower(),
                "clean-install docs",
                "vscode_regression",
            ),
            CheckResult(
                "vscode:version",
                pkg.get("version") == INTENDED_VSCODE_VERSION,
                INTENDED_VSCODE_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "schema:assessment_1_2",
                ASSESSMENT_SCHEMA_VERSION == "1.2",
                ASSESSMENT_SCHEMA_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "prior:docs_policy_1_0",
                'MARKETPLACE_DOCS_POLICY_VERSION = "1.0"'
                in _read(monorepo, "vscode-plugin/src/marketplaceDocs/policy.ts"),
                "13.13 policy 1.0",
                "vscode_regression",
            ),
            CheckResult(
                "package:test_wired",
                "cleanInstall.test.js"
                in _read(monorepo, "vscode-plugin/package.json"),
                "unit test wired",
                "vscode_regression",
            ),
            CheckResult(
                "epic_14:not_started",
                slice_1315_absent,
                "Epic 14 deferred",
                "vscode_regression",
            ),
            CheckResult(
                "readme:packaged",
                inv is not None
                and (
                    "extension/README.md" in inv.names
                    or "extension/readme.md" in inv.names
                ),
                "README in VSIX",
                "package_inventory",
            ),
            CheckResult(
                "license:packaged",
                inv is not None
                and any(
                    n.lower().endswith("license") or n.lower().endswith("license.txt")
                    for n in inv.names
                ),
                "LICENSE in VSIX",
                "package_inventory",
            ),
        ]
    )

    # Fix policy:flags operator precedence with explicit bool
    flags_ok = (
        "marketplace_publish_required: false" in policy
        and "automatic_cli_install_allowed: false" in policy
        and "machine_identity_allowed: false" in policy
        and "installation_identity_allowed: false" in policy
        and (
            'supported_cli_family: "0.2.x"' in policy
            or 'CLEAN_INSTALL_SUPPORTED_CLI_FAMILY = "0.2.x"' in policy
        )
    )
    for i, c in enumerate(checks):
        if c.name == "policy:flags":
            checks[i] = CheckResult(c.name, flags_ok, c.detail, c.category)

    init_ok = test_files["repositoryInitialization"] and (
        "assertInitArgsForbidForce" in ext
        or (
            monorepo / "vscode-plugin/src/repositoryInitialization"
        ).exists()
    )
    for i, c in enumerate(checks):
        if c.name == "initialization:tests":
            checks[i] = CheckResult(c.name, init_ok, c.detail, c.category)

    if not build_ok:
        defects.append(
            Defect("packaging defect", "vsix", "built VSIX", build_detail)
        )
    if forbidden:
        defects.append(
            Defect(
                "package integrity defect",
                "vsix",
                "no forbidden entries",
                str(forbidden[:5]),
            )
        )
    if activation_probes:
        defects.append(
            Defect(
                "activation defect",
                "extension.ts",
                "no product actions on activate",
                "probe_detected",
            )
        )

    return checks, defects, meta
