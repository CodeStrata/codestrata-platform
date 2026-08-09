"""Contract for Slice 13.1 VS Code Community workflow verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_community_workflow import (
    VSCODE_COMMUNITY_WORKFLOW_ID,
    VSCODE_COMMUNITY_WORKFLOW_VERSION,
)

SCHEMA_NAME = "vscode-community-workflow-verification"
SCHEMA_VERSION = "1.0.0"

SV131_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv13-1"
REPORT_JSON = "vscode-community-workflow-verification.json"
REPORT_MD = "vscode-community-workflow-verification.md"

WORKFLOW_POLICY_ID = "community-vscode-workflow-policy"
WORKFLOW_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"

WORKFLOW_COMMANDS = (
    "codestrata.init",
    "codestrata.assess",
    "codestrata.assessWithAi",
    "codestrata.openHtmlReport",
)

WORKFLOW_OPERATIONS = (
    "initialize_repository",
    "run_assessment",
    "run_assessment_with_ai",
    "open_report",
)

WORKFLOW_PACKAGE = "vscode-plugin/src/communityWorkflow"

ALLOWED_LIMITATIONS = frozenset(
    {
        "progress_ui_retained_until_13_6",
        "report_opening_ux_retained_until_13_7",
        "recovery_framework_active_13_8",
        "version_compatibility_active_13_11",
        "marketplace_complete_via_13_12_13_13",
        "no_full_extension_host_ui_automation",
        "worktree_uncommitted",
        "activation_uses_onStartupFinished_with_lightweight_side_effects",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv131Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_COMMUNITY_WORKFLOW_ID
    package_version: str = VSCODE_COMMUNITY_WORKFLOW_VERSION
    start_slice_13_2: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv131Contract:
    return Sv131Contract()
