"""Contract for Slice 17.27 — Epic 17 Completion Verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-epic17-completion-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-epic17-completion-verification"
VERSION = "1.0.0"
SUITE_ID = "sv17-27"
SV1727_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-27"
REPORT_JSON = "community-epic17-completion-verification.json"
REPORT_MD = "community-epic17-completion-verification.md"

POLICY_RELATIVE = "platform/policies/community_epic17_completion_policy.json"
POLICY_SCHEMA = "community-epic17-completion-policy:1.0"
DEFECT_REGISTER_RELATIVE = "platform/policies/community_epic17_defect_register.json"
CARRY_FORWARD_RELATIVE = (
    "platform/policies/community_epic17_release_carry_forward_register.json"
)
CONTRACT_RELATIVE = "platform/contracts/community_epic17_completion_verification.json"
WORKFLOW_REGISTER_RELATIVE = "platform/policies/platform_workflow_authority_register.json"
CAPABILITY_MAP_RELATIVE = (
    ".codestrata-artifacts/validation/suites/sv17-27/epic17-capability-map.json"
)
LIVE_CACHE_RELATIVE = (
    ".codestrata-artifacts/validation/suites/sv17-27/live-probe-cache.json"
)
ZERO_DRIFT_RELATIVE = (
    ".codestrata-artifacts/validation/suites/sv17-27/tofu-plan-zero-drift.json"
)
EXPORT_EVIDENCE_RELATIVE = (
    ".codestrata-artifacts/validation/suites/sv17-22/export-dry-run-evidence.json"
)
SECURITY_SCAN_RELATIVE = (
    ".codestrata-artifacts/validation/suites/sv17-27/security-scan.json"
)
TRANSPARENCY_HANDOFF_RELATIVE = (
    ".codestrata-artifacts/validation/suites/sv17-27/transparency-documentation-handoff.json"
)

PRIOR_SUITE_PACKAGES: dict[str, str] = {
    "sv17-12": "community_artifact_consolidation",
    "sv17-13": "community_22_repository_validation",
    "sv17-14": "community_api_domain",
    "sv17-15": "report_artifact_lifecycle",
    "sv17-16": "community_report_publishing",
    "sv17-17": "community_telemetry_consent",
    "sv17-18": "community_data_lake_insights",
    "sv17-19": "community_assessment_engineering_intelligence",
    "sv17-20": "community_ai_providers",
    "sv17-21": "community_vscode_clean_install",
    "sv17-22": "community_epic17_defect_resolution",
    "sv17-23": "community_status_report_registry",
    "sv17-24": "community_insights_production_auth",
    "sv17-25": "community_status_workflow_cleanup",
    "sv17-26": "community_public_documentation_reconciliation",
}

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "production_cloud_live": True,
    "api_domain_live": True,
    "reports_domain_live": True,
    "docs_live": True,
    "insights_live": True,
    "telemetry_consent_validated": True,
    "production_ingestion_validated": True,
    "data_lake_validated": True,
    "insights_aggregation_validated": True,
    "assessment_reports_validated": True,
    "engineering_intelligence_validated": True,
    "report_publishing_validated": True,
    "vscode_candidate_validated": True,
    "bedrock_e2e_validated": True,
    "openai_owner_credential_requirement_explicit": True,
    "openrouter_owner_credential_requirement_explicit": True,
    "production_zero_drift": True,
    "release_carry_forwards_explicit": True,
    "epic17_feature_work_complete": True,
    "feature_freeze": True,
    "new_features_forbidden": True,
    "no_cli_publish": True,
    "no_vscode_marketplace_publish": True,
    "no_release_tag": True,
    "no_release_commit": True,
    "no_full_22_repository_release_corpus": True,
    "start_slice_17_27": True,
    "start_transparency_documentation_epic": False,
    "start_release_readiness_epic": False,
}

SOFT_LIMITATION_CODES = frozenset(
    {
        "codestrata_ai_favicon_stale_must_fix_before_release",
        "github_v0_1_0_release_expected_gap",
        "openai_owner_credential_required",
        "openrouter_owner_credential_required",
        "full_22_corpus_deferred_to_release",
        "marketplace_publish_deferred",
        "cli_publish_deferred",
        "infrastructure_export_blocked_by_local_tfvars",
        "ai_usage_construction_only_deferred",
        "owner_pat_rotation_if_exposed",
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "export_repo_sync_deferred",
    }
)

ALLOWED_DEFECT_STATUSES = frozenset(
    {
        "RESOLVED",
        "RELEASE_CARRY_FORWARD",
        "OWNER_ACTION_REQUIRED",
        "BLOCKER",
    }
)

FORBIDDEN_NEXT_PACKAGES = (
    "verification/community_transparency_documentation",
    "verification/community_release_readiness",
    "verification/community_marketplace_publish",
    "verification/community_cli_publish",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1727Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_27: bool = True
    start_transparency_documentation_epic: bool = False
    start_release_readiness_epic: bool = False


def default_contract() -> Sv1727Contract:
    return Sv1727Contract()
