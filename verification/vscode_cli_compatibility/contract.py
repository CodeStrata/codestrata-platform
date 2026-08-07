"""Contract for Slice 13.11 CLI–extension compatibility verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_cli_compatibility import (
    VSCODE_CLI_COMPATIBILITY_ID,
    VSCODE_CLI_COMPATIBILITY_VERSION,
)

SCHEMA_NAME = "vscode-cli-compatibility-verification"
SCHEMA_VERSION = "1.0.0"
SV1311_OUTPUT_RELATIVE = "reports/verification/sv13-11"
REPORT_JSON = "vscode-cli-compatibility-verification.json"
REPORT_MD = "vscode-cli-compatibility-verification.md"

COMPAT_POLICY_ID = "community-vscode-cli-compatibility-policy"
COMPAT_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"
COMPAT_PACKAGE = "vscode-plugin/src/cliCompatibility"

ALLOWED_LIMITATIONS = frozenset(
    {
        "matrix_covers_extension_0_2_0_cli_0_2_x",
        "future_matrix_expansion_possible",
        "no_full_extension_host_ui_automation",
        "marketplace_complete_via_13_12_13_13",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1311Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_CLI_COMPATIBILITY_ID
    package_version: str = VSCODE_CLI_COMPATIBILITY_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv1311Contract:
    return Sv1311Contract()
