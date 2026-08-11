"""Contract for Slice 18.8 — Epic 18 Transparency Documentation Completion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-epic18-completion-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-epic18-completion-verification"
VERSION = "1.0.0"
SUITE_ID = "sv18-8"
SV188_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv18-8"
REPORT_JSON = "community-epic18-completion-verification.json"
REPORT_MD = "community-epic18-completion-verification.md"

POLICY_RELATIVE = "platform/policies/community_epic18_completion_policy.json"
POLICY_SCHEMA = "community-epic18-completion-policy:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_epic18_completion_verification.json"
CARRY_FORWARD_RELATIVE = (
    "platform/policies/community_epic18_release_carry_forward_register.json"
)
EVIDENCE_INVENTORY_RELATIVE = (
    "platform/policies/community_epic18_evidence_inventory_register.json"
)
CLAIM_REGISTER_RELATIVE = (
    "platform/policies/community_public_claim_runtime_validation_register.json"
)
CONTRADICTION_REGISTER_RELATIVE = (
    "platform/policies/community_transparency_contradiction_register.json"
)
WORKFLOW_REGISTER_RELATIVE = "platform/policies/platform_workflow_authority_register.json"
PUBLIC_CLIENT_REGISTER_RELATIVE = (
    "platform/policies/community_public_client_credential_register.json"
)
REPORT_PUBLISH_POLICY_RELATIVE = (
    "platform/policies/community_report_publishing_policy.json"
)

ENGINE_REPORT_PUBLISHING = "engine/src/codestrata/community_cloud/report_publishing.py"
ENGINE_PUBLIC_CLIENT = "engine/src/codestrata/community_cloud/public_client_credential.py"
ENGINE_REPORT_CLI = "engine/src/codestrata/cli/report.py"
PLATFORM_REPORT_SERVICE = (
    "platform/src/codestrata_platform/community_cloud_api/reports/service.py"
)
PLATFORM_ERRORS = "platform/src/codestrata_platform/community_cloud_api/errors.py"
REPORTS_WORKER = "reports/workers/delivery.ts"
VSCODE_POLICY = "vscode-plugin/src/reportPublishing/policy.ts"
RETENTION_DOC = "docs/security/retention-and-deletion.md"
DATA_COLLECTION_DOC = "docs/security/data-collection.md"
SOURCE_LOCALITY_DOC = "docs/security/source-locality.md"
CLI_DOC = "docs/reference/cli.md"
ROOT_README = "README.md"
ROOT_SECURITY = "SECURITY.md"
ENGINE_README = "engine/README.md"
VSCODE_README = "vscode-plugin/README.md"

PRIOR_SUITE_PACKAGES: dict[str, str] = {
    "sv18-1": "community_transparency_inventory",
    "sv18-2": "community_telemetry_data_transparency",
    "sv18-3": "community_privacy_retention_optout",
    "sv18-4": "community_ai_source_locality",
    "sv18-5": "community_cloud_architecture_transparency",
    "sv18-6": "community_public_surface_reconciliation",
    "sv18-7": "community_public_claim_runtime_validation",
}

# Claim-count baseline from first Slice 18.7 closure before 18.7A additions.
SV187_PRIOR_CLAIM_COUNT = 68
# Current authoritative inventory after 18.7A (C18-7-016, C18-7-017).
SV187_CURRENT_CLAIM_COUNT = 70
CLAIM_COUNT_DELTA_NOTES = (
    "C18-7-016 added for interactive publish/packaged public client journey",
    "C18-7-017 added for independent public GET proof after publish (T18-C007)",
)

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "transparency_inventory_validated": True,
    "telemetry_data_collection_validated": True,
    "privacy_retention_optout_validated": True,
    "ai_source_locality_validated": True,
    "community_cloud_architecture_validated": True,
    "public_surface_reconciliation_validated": True,
    "public_claims_runtime_validated": True,
    "report_publish_journey_validated": True,
    "contradictions_classified": True,
    "claim_inventory_complete": True,
    "publish_independent_of_telemetry": True,
    "public_get_independent_of_publish_post": True,
    "packaged_public_client_documented": True,
    "release_carry_forwards_explicit": True,
    "epic18_transparency_work_complete": True,
    "feature_freeze": True,
    "new_features_forbidden": True,
    "no_cli_publish": True,
    "no_vscode_marketplace_publish": True,
    "no_release_tag": True,
    "no_release_commit": True,
    "no_full_22_repository_release_corpus": True,
    "no_silent_community_cloud_redeploy": True,
    "no_manufactured_owner_e2e": True,
    "start_slice_18_8": True,
    "start_release_readiness_epic": False,
}

FORBIDDEN_EPIC19_PACKAGES = (
    "verification/community_release_readiness",
    "verification/community_release_readiness_publication",
    "verification/release_readiness",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "report_not_found_live_message_pending_redeploy",
        "marketplace_unpublished",
        "openai_owner_credential_required",
        "openrouter_owner_credential_required",
        "github_release_still_0_1_0",
        "website_favicon_deferred",
        "worktree_uncommitted",
        "infra_zero_drift_soft",
        "full_release_corpus_deferred",
        "deferred_telemetry_producers",
        "monorepo_pre_cutover_authority",
    }
)

STALE_PHRASE_NEEDLES = (
    "CODESTRATA_TELEMETRY_OPT_IN",
    "must set CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL",
    "AWS credentials are required to publish",
    "report URLs are permanent",
    "telemetry is required to publish",
)

SLICE_MATRIX_SPEC: dict[str, dict[str, str]] = {
    "18.1": {
        "purpose": "Build Authoritative Transparency Inventory",
        "suite": "sv18-1",
    },
    "18.2": {
        "purpose": "Telemetry + Data Collection Documentation",
        "suite": "sv18-2",
    },
    "18.3": {
        "purpose": "Privacy + Retention + Opt-Out Documentation",
        "suite": "sv18-3",
    },
    "18.4": {
        "purpose": "AI Provider + Source-Locality Documentation",
        "suite": "sv18-4",
    },
    "18.5": {
        "purpose": "Community Cloud / Data Lake / Insights / API Architecture",
        "suite": "sv18-5",
    },
    "18.6": {
        "purpose": "README / SECURITY / CLI / VS Code / Docs Reconciliation",
        "suite": "sv18-6",
    },
    "18.7": {
        "purpose": "Public Claims vs Runtime Validation",
        "suite": "sv18-7",
    },
    "18.7A": {
        "purpose": "Community report-publishing journey correction",
        "suite": "sv18-7 overlay + engine report_publishing",
    },
    "18.8": {
        "purpose": "Transparency Epic Completion Verification",
        "suite": "sv18-8",
    },
}


@dataclass(frozen=True, slots=True)
class Contract:
    start_slice_18_8: bool = True
    start_release_readiness_epic: bool = False
    no_cli_publish: bool = True
    no_vscode_marketplace_publish: bool = True
    no_release_tag: bool = True
    no_full_22_repository_release_corpus: bool = True


def default_contract() -> Contract:
    return Contract()


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]
