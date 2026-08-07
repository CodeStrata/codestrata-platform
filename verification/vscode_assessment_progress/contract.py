"""Contract for Slice 13.6 VS Code assessment progress verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_assessment_progress import (
    VSCODE_ASSESSMENT_PROGRESS_ID,
    VSCODE_ASSESSMENT_PROGRESS_VERSION,
)

SCHEMA_NAME = "vscode-assessment-progress-verification"
SCHEMA_VERSION = "1.0.0"
SV136_OUTPUT_RELATIVE = "reports/verification/sv13-6"
REPORT_JSON = "vscode-assessment-progress-verification.json"
REPORT_MD = "vscode-assessment-progress-verification.md"

PROGRESS_POLICY_ID = "community-vscode-assessment-progress-policy"
PROGRESS_POLICY_VERSION = "1.0"
ASSESSMENT_EXECUTION_POLICY_VERSION = "1.0"
WORKFLOW_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"

PROGRESS_PACKAGE = "vscode-plugin/src/assessmentProgress"

ALLOWED_LIMITATIONS = frozenset(
    {
        "indeterminate_progress_only",
        "no_engine_structured_progress_protocol",
        "process_cancellation_mechanism_retained",
        "report_opening_complete_via_13_7",
        "recovery_framework_available_via_13_8",
        "no_full_extension_host_ui_automation",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv136Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_ASSESSMENT_PROGRESS_ID
    package_version: str = VSCODE_ASSESSMENT_PROGRESS_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv136Contract:
    return Sv136Contract()
