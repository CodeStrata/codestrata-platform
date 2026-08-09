"""Contract for Slice 13.5 VS Code assessment execution verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_assessment_execution import (
    VSCODE_ASSESSMENT_EXECUTION_ID,
    VSCODE_ASSESSMENT_EXECUTION_VERSION,
)

SCHEMA_NAME = "vscode-assessment-execution-verification"
SCHEMA_VERSION = "1.0.0"
SV135_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv13-5"
REPORT_JSON = "vscode-assessment-execution-verification.json"
REPORT_MD = "vscode-assessment-execution-verification.md"

ASSESSMENT_POLICY_ID = "community-vscode-assessment-execution-policy"
ASSESSMENT_POLICY_VERSION = "1.0"
WORKFLOW_POLICY_VERSION = "1.0"
DISCOVERY_POLICY_VERSION = "1.0"
INSTALLATION_POLICY_VERSION = "1.0"
INIT_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"

ASSESSMENT_PACKAGE = "vscode-plugin/src/assessmentExecution"
ENGINE_ASSESS = "engine/src/codestrata/cli/assess.py"

ALLOWED_LIMITATIONS = frozenset(
    {
        "progress_complete_via_13_6",
        "report_opening_complete_via_13_7",
        "recovery_framework_available_via_13_8",
        "assessment_timeout_not_invented",
        "no_live_ai_provider_calls_in_tests",
        "no_full_extension_host_ui_automation",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv135Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_ASSESSMENT_EXECUTION_ID
    package_version: str = VSCODE_ASSESSMENT_EXECUTION_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv135Contract:
    return Sv135Contract()
