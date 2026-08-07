"""Focused static checks for Slice 13.8 failure recovery."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_failure_recovery.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    INTENDED_VSCODE_VERSION,
    RECOVERY_PACKAGE,
    RECOVERY_POLICY_ID,
    RECOVERY_POLICY_VERSION,
)
from verification.vscode_failure_recovery.models import CheckResult, Defect


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def _pkg_version(monorepo: Path) -> str:
    text = _read(monorepo, "vscode-plugin/package.json")
    match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
    return match.group(1) if match else ""


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = _read(monorepo, f"{RECOVERY_PACKAGE}/policy.ts")
    catalog = _read(monorepo, f"{RECOVERY_PACKAGE}/catalog.ts")
    presentation = _read(monorepo, f"{RECOVERY_PACKAGE}/presentation.ts")
    categories = _read(monorepo, f"{RECOVERY_PACKAGE}/categories.ts")
    diagnostics = _read(monorepo, f"{RECOVERY_PACKAGE}/diagnostics.ts")
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    docs = _read(monorepo, "vscode-plugin/docs/failure-recovery.md")
    workflow_policy = _read(monorepo, "vscode-plugin/src/communityWorkflow/policy.ts")

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                RECOVERY_POLICY_ID in policy and RECOVERY_POLICY_VERSION in policy,
                f"{RECOVERY_POLICY_ID}:{RECOVERY_POLICY_VERSION}",
                "recovery_policy",
            ),
            CheckResult(
                "policy:no_auto",
                "automatic_recovery_execution_allowed: false" in policy
                and "automatic_retry_allowed: false" in policy
                and "automatic_install_allowed: false" in policy
                and "automatic_assessment_rerun_allowed: false" in policy
                and "automatic_report_reopen_allowed: false" in policy,
                "auto recovery forbidden",
                "auto_execute_forbidden",
            ),
            CheckResult(
                "policy:privacy",
                "stack_traces_allowed: false" in policy
                and "paths_allowed: false" in policy
                and "cli_output_in_messages_allowed: false" in policy
                and "credentials_allowed: false" in policy,
                "privacy flags",
                "privacy",
            ),
            CheckResult(
                "catalog:domains",
                '"workspace"' in categories
                and '"assessment"' in categories
                and '"secondary_failure"' in categories,
                "failure domains",
                "catalog",
            ),
            CheckResult(
                "catalog:actions",
                "Initialize Repository" in categories
                and "Install CLI" in categories
                and "Run Assessment Again" in categories
                and "Open Report" in categories,
                "recovery action labels",
                "catalog",
            ),
            CheckResult(
                "catalog:mappings",
                "repository_not_initialized" in catalog
                and "assessment_failed" in catalog
                and "report_not_found" in catalog
                and "assessment_cancelled" in catalog,
                "failure mappings",
                "catalog",
            ),
            CheckResult(
                "presentation:no_auto_dispatch",
                "Never auto-execute" in presentation
                or "never auto-execute" in presentation.lower(),
                "user-triggered dispatch only",
                "presentation",
            ),
            CheckResult(
                "presentation:api",
                "presentFailureRecovery" in presentation
                and "executeCommand" in presentation,
                "presentation API",
                "presentation",
            ),
            CheckResult(
                "extension:wired",
                "presentFailureRecovery" in ext
                and "createVsCodeRecoveryHost" in ext
                and "failureRecovery" in ext,
                "extension wiring",
                "presentation",
            ),
            CheckResult(
                "primary:assessment_failed",
                'failureCategory: "assessment_failed"' in ext
                or "assessment_failed" in ext,
                "assessment failure recovery",
                "primary_authority",
            ),
            CheckResult(
                "secondary:report_not_found",
                'failureCategory: "report_not_found"' in ext
                and "primaryExit: \"success\"" in ext,
                "report missing preserves success",
                "secondary_isolation",
            ),
            CheckResult(
                "cancel:no_retry_action",
                'failureCategory: "assessment_cancelled"' in ext
                and 'recovery_action: "none"' in catalog,
                "cancel has no recovery action",
                "primary_authority",
            ),
            CheckResult(
                "privacy:diagnostics",
                "recoveryDiagnosticsContainForbiddenKeys" in diagnostics,
                "privacy helper",
                "privacy",
            ),
            CheckResult(
                "telemetry:forbidden",
                "telemetry_allowed: false" in policy,
                "no recovery telemetry",
                "telemetry_boundary",
            ),
            CheckResult(
                "analytics:forbidden",
                "analytics_allowed: false" in policy,
                "no recovery analytics",
                "analytics_boundary",
            ),
            CheckResult(
                "docs:present",
                (monorepo / "vscode-plugin/docs/failure-recovery.md").is_file()
                and "never" in docs.lower()
                and "automatically" in docs.lower(),
                "docs present",
                "privacy",
            ),
            CheckResult(
                "workflow:limitation_updated",
                "recovery_framework_active_13_8" in workflow_policy,
                "workflow limitation updated",
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
                "package:json_test",
                "failureRecovery.test.js" in _read(monorepo, "vscode-plugin/package.json"),
                "unit test wired",
                "vscode_regression",
            ),
            CheckResult(
                "prior_policies:unchanged_version",
                '"1.0"' in _read(monorepo, "vscode-plugin/src/reportOpening/policy.ts")
                and "REPORT_OPENING_POLICY_VERSION = \"1.0\""
                in _read(monorepo, "vscode-plugin/src/reportOpening/policy.ts"),
                "prior report policy 1.0",
                "vscode_regression",
            ),
        ]
    )

    if not all(c.ok for c in checks if c.category == "auto_execute_forbidden"):
        defects.append(
            Defect(
                "auto-execute defect",
                "recovery",
                "never auto",
                "auto executed",
            )
        )
    if not all(c.ok for c in checks if c.category == "privacy"):
        defects.append(
            Defect(
                "privacy/diagnostics defect",
                "diagnostics",
                "safe",
                "leaked",
            )
        )

    # Ensure package.json version parse works for reporting
    _ = json.loads(_read(monorepo, "vscode-plugin/package.json"))

    return checks, defects
