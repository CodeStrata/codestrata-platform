"""Contract for Slice 13.4 VS Code repository initialization verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_repository_initialization import (
    VSCODE_REPOSITORY_INITIALIZATION_ID,
    VSCODE_REPOSITORY_INITIALIZATION_VERSION,
)

SCHEMA_NAME = "vscode-repository-initialization-verification"
SCHEMA_VERSION = "1.0.0"
SV134_OUTPUT_RELATIVE = "reports/verification/sv13-4"
REPORT_JSON = "vscode-repository-initialization-verification.json"
REPORT_MD = "vscode-repository-initialization-verification.md"

INIT_POLICY_ID = "community-vscode-repository-initialization-policy"
INIT_POLICY_VERSION = "1.0"
WORKFLOW_POLICY_VERSION = "1.0"
DISCOVERY_POLICY_VERSION = "1.0"
INSTALLATION_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"

INIT_PACKAGE = "vscode-plugin/src/repositoryInitialization"
ENGINE_INIT = "engine/src/codestrata/cli/init_cmd.py"

ALLOWED_LIMITATIONS = frozenset(
    {
        "engine_init_output_retained",
        "multi_root_selection_ux_retained",
        "cancellation_ui_not_redesigned",
        "recovery_framework_available_via_13_8",
        "no_full_extension_host_ui_automation",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv134Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_REPOSITORY_INITIALIZATION_ID
    package_version: str = VSCODE_REPOSITORY_INITIALIZATION_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv134Contract:
    return Sv134Contract()
