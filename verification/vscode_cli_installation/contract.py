"""Contract for Slice 13.3 VS Code CLI installation verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_cli_installation import (
    VSCODE_CLI_INSTALLATION_ID,
    VSCODE_CLI_INSTALLATION_VERSION,
)

SCHEMA_NAME = "vscode-cli-installation-verification"
SCHEMA_VERSION = "1.0.0"
SV133_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv13-3"
REPORT_JSON = "vscode-cli-installation-verification.json"
REPORT_MD = "vscode-cli-installation-verification.md"

INSTALLATION_POLICY_ID = "community-vscode-cli-installation-policy"
INSTALLATION_POLICY_VERSION = "1.0"
DISCOVERY_POLICY_VERSION = "1.0"
WORKFLOW_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"
APPROACH_DECISION = "guidance_only"

INSTALLATION_PACKAGE = "vscode-plugin/src/cliInstallation"

METHOD_IDS = (
    "documentation",
    "python_package",
    "pipx",
    "uv_tool",
    "terminal_guidance",
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "guidance_only_approach",
        "cli_install_guidance_complete_via_13_3",
        "compatibility_matrix_active_via_13_11",
        "platform_guidance_validated_via_mocks",
        "no_full_extension_host_ui_automation",
        "terminal_opened_without_auto_execute",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv133Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_CLI_INSTALLATION_ID
    package_version: str = VSCODE_CLI_INSTALLATION_VERSION
    approach: str = APPROACH_DECISION
    start_slice_13_4: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv133Contract:
    return Sv133Contract()
