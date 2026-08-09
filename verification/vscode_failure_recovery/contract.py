"""Contract for Slice 13.8 VS Code failure recovery verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_failure_recovery import (
    VSCODE_FAILURE_RECOVERY_ID,
    VSCODE_FAILURE_RECOVERY_VERSION,
)

SCHEMA_NAME = "vscode-failure-recovery-verification"
SCHEMA_VERSION = "1.0.0"
SV138_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv13-8"
REPORT_JSON = "vscode-failure-recovery-verification.json"
REPORT_MD = "vscode-failure-recovery-verification.md"

RECOVERY_POLICY_ID = "community-vscode-recovery-policy"
RECOVERY_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"
RECOVERY_PACKAGE = "vscode-plugin/src/failureRecovery"

ALLOWED_LIMITATIONS = frozenset(
    {
        "user_triggered_actions_only",
        "no_automatic_retry",
        "no_full_extension_host_ui_automation",
        "marketplace_complete_via_13_12_13_13",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv138Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_FAILURE_RECOVERY_ID
    package_version: str = VSCODE_FAILURE_RECOVERY_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv138Contract:
    return Sv138Contract()
