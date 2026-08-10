"""Contract for Slice 17.22 — Epic 17 defect resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-epic17-defect-resolution-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-epic17-defect-resolution-verification"
VERSION = "1.0.0"
SUITE_ID = "sv17-22"
SV1722_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-22"
REPORT_JSON = "community-epic17-defect-resolution-verification.json"
REPORT_MD = "community-epic17-defect-resolution-verification.md"

POLICY_RELATIVE = "platform/policies/community_epic17_defect_resolution_policy.json"
POLICY_SCHEMA = "community-epic17-defect-resolution-policy:1.0"
DEFECT_REGISTER_RELATIVE = "platform/policies/community_epic17_defect_register.json"
DEFECT_REGISTER_SCHEMA = "community-epic17-defect-register:1.0"
CARRY_FORWARD_RELATIVE = (
    "platform/policies/community_epic17_release_carry_forward_register.json"
)
CARRY_FORWARD_SCHEMA = "community-epic17-release-carry-forward-register:1.0"
CONTRACT_RELATIVE = (
    "platform/contracts/community_epic17_defect_resolution_verification.json"
)

EXPECTED_17_21_PACKAGE = "verification/community_vscode_clean_install"
EXPECTED_17_22_PACKAGE = "verification/community_epic17_defect_resolution"
EXPECTED_17_23_PACKAGE = "verification/community_status_report_registry"

# 17.23 is active; forbid premature 17.24 packages.
SLICE_17_24_PACKAGE_CANDIDATES = (
    "verification/community_production_slice_17_24",
    "verification/community_release_epic",
    "verification/community_marketplace_publish",
)

# Retained alias — historical name; checks now gate 17.24.
SLICE_17_23_PACKAGE_CANDIDATES = SLICE_17_24_PACKAGE_CANDIDATES

PUBLIC_API = "https://api.codestrata.ai"
PUBLIC_API_HEALTH = "https://api.codestrata.ai/api/v1/health"
PUBLIC_REPORTS = "https://reports.codestrata.ai"
PUBLIC_DOCS = "https://docs.codestrata.ai"
PUBLIC_INSIGHTS = "https://insights.codestrata.ai"

PUBLIC_REPORT_URLS_RELATIVE = (
    ".codestrata-artifacts/validation/suites/release-v0.2.0/public-report-urls.json"
)

SETTINGS_POLICIES_PY = "engine/src/codestrata/ai/providers/settings_policies.py"
CLONE_PY = "engine/verification/repository_assessment/clone.py"
LIFECYCLE_TF = "infrastructure/modules/community-data-lake/lifecycle.tf"
DOCS_AI_PROVIDERS = "docs/ai-providers/index.md"

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "feature_freeze": True,
    "new_features_forbidden": True,
    "known_blockers_resolved": True,
    "security_blockers_resolved": True,
    "production_zero_drift": True,
    "cross_repo_exports_clean": True,
    "release_carry_forwards_explicit": True,
    "start_slice_17_22": True,
    "start_slice_17_23": True,
    "start_slice_17_24": False,
}

SOFT_LIMITATION_CODES = frozenset(
    {
        "infrastructure_export_blocked_by_local_tfvars",
        "openai_key_unavailable",
        "openrouter_key_unavailable",
        "full_extension_host_ui_automation_deferred",
        "full_22_corpus_deferred_to_release",
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "ai_usage_construction_only_deferred",
        "owner_pat_rotation_if_exposed",
        "github_temporary_unavailable_handled",
        "status_api_deploy_pending",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1722Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_22: bool = True
    start_slice_17_23: bool = True
    start_slice_17_24: bool = False


def default_contract() -> Sv1722Contract:
    return Sv1722Contract()
