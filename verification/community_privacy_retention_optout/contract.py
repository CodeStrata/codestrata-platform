"""Contract for Slice 18.3 — Privacy + Retention + Opt-Out Documentation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-privacy-retention-optout-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-privacy-retention-optout-verification"
VERSION = "1.0.0"
SUITE_ID = "sv18-3"
SV183_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv18-3"
REPORT_JSON = "community-privacy-retention-optout-verification.json"
REPORT_MD = "community-privacy-retention-optout-verification.md"

POLICY_RELATIVE = "platform/policies/community_privacy_retention_optout_policy.json"
CONTRACT_RELATIVE = (
    "platform/contracts/community_privacy_retention_optout_verification.json"
)
WORKFLOW_REGISTER_RELATIVE = "platform/policies/platform_workflow_authority_register.json"
CONTRADICTION_REGISTER_RELATIVE = (
    "platform/policies/community_transparency_contradiction_register.json"
)
RETENTION_REGISTER_RELATIVE = "platform/policies/community_retention_register.json"
OPT_OUT_REGISTER_RELATIVE = "platform/policies/community_opt_out_deletion_register.json"
CLAIM_REGISTER_RELATIVE = (
    "platform/policies/community_privacy_retention_optout_claim_register.json"
)
DATA_LAKE_LIFECYCLE = "infrastructure/modules/community-data-lake/lifecycle.tf"
DATA_LAKE_VARIABLES = "infrastructure/modules/community-data-lake/variables.tf"

PRIVACY_DOC = "docs/security/privacy.md"
RETENTION_DOC = "docs/security/retention-and-deletion.md"
DATA_COLLECTION_DOC = "docs/security/data-collection.md"
TELEMETRY_DOC = "docs/reference/telemetry.md"
CLI_DOC = "docs/reference/cli.md"
VSCODE_DOC = "docs/extensions/vscode.md"
ENGINE_PRIVACY = "engine/PRIVACY.md"
VSCODE_PRIVACY = "vscode-plugin/PRIVACY.md"

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "local_artifact_retention_documented": True,
    "report_retention_documented": True,
    "data_lake_retention_documented": True,
    "identity_retention_documented": True,
    "opt_out_scope_documented": True,
    "historical_telemetry_not_auto_deleted_documented": True,
    "report_revoke_documented": True,
    "local_delete_user_controlled": True,
    "self_service_historical_deletion_not_claimed": True,
    "telemetry_consent_separate_from_publish": True,
    "third_party_ai_retention_not_speculated": True,
    "t18_c005_resolved": True,
    "start_slice_18_3": True,
    "start_slice_18_4": False,
    "no_cli_publish": True,
    "no_vscode_marketplace_publish": True,
    "no_release_tag": True,
    "no_full_22_repository_release_corpus": True,
    "no_runtime_redesign": True,
    "no_deletion_feature_added": True,
}

FORBIDDEN_18_4_PACKAGES = (
    "verification/community_ai_provider_transparency",
    "verification/community_slice_18_4",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "no_self_service_historical_telemetry_deletion",
        "no_self_service_identity_deletion",
        "third_party_ai_retention_deferred_to_provider_terms_or_18_4",
        "marketplace_content_not_published",
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "live_docs_unreachable",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv183Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_18_3: bool = True
    start_slice_18_4: bool = False


def default_contract() -> Sv183Contract:
    return Sv183Contract()
