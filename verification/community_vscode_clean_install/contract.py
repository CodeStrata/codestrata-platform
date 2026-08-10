"""Contract for Slice 17.21 — VS Code clean install validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-vscode-clean-install-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-vscode-clean-install-verification"
VERSION = "1.0.0"
SUITE_ID = "sv17-21"
SV1721_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-21"
REPORT_JSON = "community-vscode-clean-install-verification.json"
REPORT_MD = "community-vscode-clean-install-verification.md"

POLICY_RELATIVE = "platform/policies/community_vscode_clean_install_validation_policy.json"
POLICY_SCHEMA = "community-vscode-clean-install-validation-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_vscode_validation_register.json"
REGISTER_SCHEMA = "community-vscode-validation-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_vscode_clean_install_verification.json"

VSCODE_PLUGIN = "vscode-plugin"
EXTENSION_PACKAGE_JSON = "vscode-plugin/package.json"
EXTENSION_VERSION = "0.2.0"
PUBLISH_COMMAND = "codestrata.publishCurrentReport"
PUBLIC_API_BASE = "https://api.codestrata.ai"
PUBLIC_REPORTS_PREFIX = "https://reports.codestrata.ai/r/"
DOCS_VSCODE = "docs/extensions/vscode.md"
PUBLIC_EXPORT_MANIFEST = "public-export-manifest.yaml"

WORK_ROOT = Path("/tmp/sv17-21-work")
WORK_USER_DATA = WORK_ROOT / "vscode-user-data"
WORK_EXTENSIONS = WORK_ROOT / "vscode-extensions"
WORK_REPO = WORK_ROOT / "flask"
WORK_ASSESS = WORK_ROOT / "assess-out"
WORK_EVIDENCE = WORK_ROOT / "evidence"

EXPECTED_17_20_PACKAGE = "verification/community_ai_providers"
EXPECTED_17_21_PACKAGE = "verification/community_vscode_clean_install"
EXPECTED_17_22_PACKAGE = "verification/community_epic17_defect_resolution"

# 17.22 is active; forbid premature 17.23 packages.
SLICE_17_23_PACKAGE_CANDIDATES = (
    "verification/community_production_slice_17_23",
    "verification/community_epic17_completion",
    "verification/community_status_api",
    "verification/community_website_status",
    "verification/community_vscode_marketplace_publish",
)

# Retained alias — historical name; checks now gate 17.23.
SLICE_17_22_PACKAGE_CANDIDATES = SLICE_17_23_PACKAGE_CANDIDATES

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "clean_profile_tested": True,
    "marketplace_publish": False,
    "engine_discovery_validated": True,
    "assessment_from_extension": True,
    "current_report_opened": True,
    "telemetry_default_off": True,
    "telemetry_opt_in_validated": True,
    "telemetry_opt_out_validated": True,
    "api_authority": "https://api.codestrata.ai",
    "explicit_report_publish_validated": True,
    "raw_s3_url_exposed": False,
    "offline_assessment_non_blocking": True,
    "start_slice_17_21": True,
    "start_slice_17_22": True,
}

SOFT_LIMITATION_CODES = frozenset(
    {
        "marketplace_publish_deferred",
        "openai_openrouter_keys_absent",
        "provider_selection_ui_deferred",
        "full_22_repo_vscode_corpus_deferred",
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "full_extension_host_ui_automation_unavailable",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1721Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_21: bool = True
    start_slice_17_22: bool = True
    start_slice_17_23: bool = False


def default_contract() -> Sv1721Contract:
    return Sv1721Contract()
