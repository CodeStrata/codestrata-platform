"""Focused static checks for Slice 13.11 CLI–extension compatibility."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_cli_compatibility.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    COMPAT_PACKAGE,
    COMPAT_POLICY_ID,
    COMPAT_POLICY_VERSION,
    INTENDED_VSCODE_VERSION,
)
from verification.vscode_cli_compatibility.models import CheckResult, Defect


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def _pkg_version(monorepo: Path) -> str:
    text = _read(monorepo, "vscode-plugin/package.json")
    match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
    return match.group(1) if match else ""


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = _read(monorepo, f"{COMPAT_PACKAGE}/policy.ts")
    matrix = _read(monorepo, f"{COMPAT_PACKAGE}/matrix.ts")
    diagnostics = _read(monorepo, f"{COMPAT_PACKAGE}/diagnostics.ts")
    discovery_compat = _read(
        monorepo, "vscode-plugin/src/cliDiscovery/compatibility.ts"
    )
    ordering = _read(
        monorepo, "vscode-plugin/src/telemetryConsentIntegration/ordering.ts"
    )
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    guidance = _read(monorepo, "vscode-plugin/src/cliInstallation/guidance.ts")
    docs = _read(monorepo, "vscode-plugin/docs/cli-compatibility.md")
    discovery_policy = _read(
        monorepo, "vscode-plugin/src/cliDiscovery/policy.ts"
    )
    unit = _read(monorepo, "vscode-plugin/src/test/cliCompatibility.test.ts")

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                COMPAT_POLICY_ID in policy and COMPAT_POLICY_VERSION in policy,
                f"{COMPAT_POLICY_ID}:{COMPAT_POLICY_VERSION}",
                "compatibility_policy",
            ),
            CheckResult(
                "policy:extension_0_2_0",
                'extension_version: "0.2.0"' in policy
                or 'COMPATIBILITY_EXTENSION_VERSION = "0.2.0"' in policy,
                "extension 0.2.0",
                "compatibility_policy",
            ),
            CheckResult(
                "matrix:0_2_x",
                'COMPATIBILITY_MINIMUM_CLI = "0.2.0"' in policy
                and "upgrade_cli" in matrix
                and "downgrade_cli" in matrix
                and "unsupported_prerelease" in matrix,
                "CLI 0.2.x matrix",
                "matrix",
            ),
            CheckResult(
                "matrix:verdicts",
                all(
                    v in matrix
                    for v in (
                        "supported",
                        "upgrade_cli",
                        "downgrade_cli",
                        "unsupported_major",
                        "unsupported_prerelease",
                        "invalid_version",
                        "unknown_version",
                    )
                ),
                "all verdicts",
                "matrix",
            ),
            CheckResult(
                "ordering:stage",
                '"cli_compatibility"' in ordering
                and ordering.find("compatible_cli")
                < ordering.find("cli_compatibility")
                < ordering.find("ai_confirmation"),
                "compatibility after discovery before AI/consent",
                "ordering",
            ),
            CheckResult(
                "workflow:stops_on_fail",
                "assessment_allowed: supported" in matrix
                or "assessment_allowed: boolean" in matrix,
                "unsupported blocks assessment",
                "workflow_integration",
            ),
            CheckResult(
                "workflow:discovery_delegates",
                "evaluateCliCompatibility" in discovery_compat,
                "discovery uses permanent matrix",
                "workflow_integration",
            ),
            CheckResult(
                "doctor:reuse",
                "doctorCompatibilityLabel" in ext
                and "Reuse discovery compatibility" in ext,
                "doctor reuses compatibility",
                "doctor_integration",
            ),
            CheckResult(
                "install:0_2_x_guidance",
                "0.2.x" in guidance and "install_supported_version" in _read(
                    monorepo, "vscode-plugin/src/cliInstallation/results.ts"
                ),
                "install guidance for unsupported",
                "installation_guidance",
            ),
            CheckResult(
                "privacy:diagnostics",
                "compatibilityDiagnosticsContainForbiddenKeys" in diagnostics
                and "probe_count: 0" in diagnostics,
                "privacy + no extra probe",
                "privacy",
            ),
            CheckResult(
                "determinism:stable_dict",
                "compatibilityDecisionToStableDict" in matrix,
                "stable serialization",
                "determinism",
            ),
            CheckResult(
                "docs:present",
                (monorepo / "vscode-plugin/docs/cli-compatibility.md").is_file()
                and "0.2.x" in docs,
                "docs present",
                "privacy",
            ),
            CheckResult(
                "discovery:limitation_updated",
                "compatibility_matrix_delegated_to_13_11" in discovery_policy
                or "compatibility_matrix" in discovery_policy,
                "discovery no longer defers matrix",
                "vscode_regression",
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
                "epic_14:not_started",
                not (monorepo / "verification" / "vscode_epic14_product_experience").exists()
                and "startEpic14ProductExperience" not in ext,
                "Epic 14 deferred",
                "vscode_regression",
            ),
            CheckResult(
                "package:test_wired",
                "cliCompatibility.test.js"
                in _read(monorepo, "vscode-plugin/package.json"),
                "unit test wired",
                "vscode_regression",
            ),
            CheckResult(
                "prior:locality_1_0",
                'SOURCE_LOCALITY_POLICY_VERSION = "1.0"'
                in _read(monorepo, "vscode-plugin/src/sourceLocality/policy.ts"),
                "13.10 policy 1.0",
                "vscode_regression",
            ),
            CheckResult(
                "errors:taxonomy",
                "cli_version_too_old" in matrix
                and "unsupported_extension_cli_pair" in matrix,
                "bounded error taxonomy",
                "matrix",
            ),
            CheckResult(
                "no_second_probe",
                "probe_count: 0" in diagnostics
                and "evaluateCliCompatibility" in matrix,
                "matrix does not spawn probes",
                "workflow_integration",
            ),
            CheckResult(
                "negative:unit_matrix",
                all(
                    needle in unit
                    for needle in (
                        '"0.1.0"',
                        '"0.3.0"',
                        '"1.0.0"',
                        '"0.2.0-rc.1"',
                        "upgrade_cli",
                        "downgrade_cli",
                        "unsupported_major",
                        "unsupported_prerelease",
                        "invalid_version",
                        "unknown_version",
                    )
                ),
                "unit negatives for matrix",
                "matrix",
            ),
            CheckResult(
                "negative:blocks_workflow",
                'const supported = verdict === "supported"' in matrix
                and "workflow_may_continue: supported" in matrix
                and "assessment_allowed: supported" in matrix
                and "telemetry_allowed: false" in matrix
                and "analytics_allowed: false" in matrix,
                "failure blocks assess/telemetry",
                "workflow_integration",
            ),
            CheckResult(
                "recovery:actions",
                all(
                    a in matrix
                    for a in (
                        "upgrade_cli",
                        "install_supported_cli",
                        "reinstall_cli",
                        "review_installation",
                    )
                ),
                "bounded recovery actions",
                "installation_guidance",
            ),
            CheckResult(
                "doctor:labels",
                all(
                    label in matrix
                    for label in (
                        "Compatible",
                        "Upgrade Required",
                        "Unsupported Version",
                        "Invalid Version",
                    )
                ),
                "doctor labels",
                "doctor_integration",
            ),
        ]
    )

    if not all(c.ok for c in checks if c.category == "matrix"):
        defects.append(
            Defect("matrix defect", "compatibility", "0.2.x", "wrong matrix")
        )

    _ = json.loads(_read(monorepo, "vscode-plugin/package.json"))
    return checks, defects
