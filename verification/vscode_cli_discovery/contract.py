"""Contract for Slice 13.2 VS Code CLI discovery verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_cli_discovery import (
    VSCODE_CLI_DISCOVERY_ID,
    VSCODE_CLI_DISCOVERY_VERSION,
)

SCHEMA_NAME = "vscode-cli-discovery-verification"
SCHEMA_VERSION = "1.0.0"

SV132_OUTPUT_RELATIVE = "reports/verification/sv13-2"
REPORT_JSON = "vscode-cli-discovery-verification.json"
REPORT_MD = "vscode-cli-discovery-verification.md"

DISCOVERY_POLICY_ID = "community-vscode-cli-discovery-policy"
DISCOVERY_POLICY_VERSION = "1.0"
WORKFLOW_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"

CLI_DISCOVERY_PACKAGE = "vscode-plugin/src/cliDiscovery"

CANDIDATE_SOURCES = (
    "explicit_configuration",
    "development_environment",
    "process_path",
    "unavailable",
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "compatibility_matrix_delegated_to_13_11",
        "installation_guidance_only_see_13_3",
        "windows_wrapper_validated_via_mocks_only",
        "no_full_extension_host_ui_automation",
        "no_live_cli_installation_test",
        "process_local_cache_omitted",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv132Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_CLI_DISCOVERY_ID
    package_version: str = VSCODE_CLI_DISCOVERY_VERSION
    start_slice_13_3: bool = True  # Slice 13.3 completed (guidance-only); keep historical field
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION
    workflow_policy_version: str = WORKFLOW_POLICY_VERSION


def default_contract() -> Sv132Contract:
    return Sv132Contract()
