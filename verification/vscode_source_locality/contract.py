"""Contract for Slice 13.10 VS Code source locality verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_source_locality import (
    VSCODE_SOURCE_LOCALITY_ID,
    VSCODE_SOURCE_LOCALITY_VERSION,
)

SCHEMA_NAME = "vscode-source-locality-verification"
SCHEMA_VERSION = "1.0.0"
SV1310_OUTPUT_RELATIVE = "reports/verification/sv13-10"
REPORT_JSON = "vscode-source-locality-verification.json"
REPORT_MD = "vscode-source-locality-verification.md"

LOCALITY_POLICY_ID = "community-vscode-source-locality-policy"
LOCALITY_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"
LOCALITY_PACKAGE = "vscode-plugin/src/sourceLocality"
SRC_ROOT = "vscode-plugin/src"

ALLOWED_LIMITATIONS = frozenset(
    {
        "ai_enabled_engine_may_use_external_configured_provider",
        "report_browser_behavior_outside_extension_not_fully_controlled",
        "static_network_dependency_verification_partly_source_based",
        "no_full_extension_host_ui_automation",
        "cli_compatibility_matrix_active_via_13_11",
        "marketplace_complete_via_13_12_13_13",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1310Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_SOURCE_LOCALITY_ID
    package_version: str = VSCODE_SOURCE_LOCALITY_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv1310Contract:
    return Sv1310Contract()
