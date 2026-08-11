"""Contract for Slice 18.1 — Community Transparency Inventory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-transparency-inventory-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-transparency-inventory-verification"
VERSION = "1.0.0"
SUITE_ID = "sv18-1"
SV181_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv18-1"
REPORT_JSON = "community-transparency-inventory-verification.json"
REPORT_MD = "community-transparency-inventory-verification.md"

POLICY_RELATIVE = "platform/policies/community_transparency_inventory_policy.json"
POLICY_SCHEMA = "community-transparency-inventory-policy:1.0"
CONTRACT_RELATIVE = (
    "platform/contracts/community_transparency_inventory_verification.json"
)
WORKFLOW_REGISTER_RELATIVE = "platform/policies/platform_workflow_authority_register.json"

REQUIRED_REGISTERS: dict[str, str] = {
    "topic": "platform/policies/community_transparency_topic_register.json",
    "fields": "platform/policies/community_telemetry_field_register.json",
    "streams": "platform/policies/community_telemetry_stream_inventory_register.json",
    "never_collected": "platform/policies/community_never_collected_register.json",
    "consent": "platform/policies/community_consent_inventory_register.json",
    "identity": "platform/policies/community_client_identity_register.json",
    "destinations": "platform/policies/community_data_destination_register.json",
    "retention": "platform/policies/community_retention_register.json",
    "api": "platform/policies/community_api_transparency_register.json",
    "ai": "platform/policies/community_ai_provider_data_flow_register.json",
    "public_docs": "platform/policies/community_public_document_register.json",
    "contradictions": "platform/policies/community_transparency_contradiction_register.json",
    "doc_authority": "platform/policies/community_documentation_authority_register.json",
    "assessment": "platform/policies/community_assessment_artifact_inventory_register.json",
    "eir": "platform/policies/community_eir_inventory_register.json",
    "publishing": "platform/policies/community_report_publishing_inventory_register.json",
    "insights": "platform/policies/community_insights_inventory_register.json",
    "source_locality": "platform/policies/community_source_locality_register.json",
    "opt_out": "platform/policies/community_opt_out_deletion_register.json",
}

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "runtime_is_documentation_source_of_truth": True,
    "all_collected_fields_inventory_required": True,
    "never_collected_claims_runtime_validated": True,
    "consent_inventory_required": True,
    "retention_matrix_required": True,
    "ai_provider_flow_inventory_required": True,
    "api_inventory_required": True,
    "source_locality_inventory_required": True,
    "public_doc_authority_defined": True,
    "start_slice_18_1": True,
    "start_slice_18_2": False,
    "no_cli_publish": True,
    "no_vscode_marketplace_publish": True,
    "no_release_tag": True,
    "no_full_22_repository_release_corpus": True,
    "no_runtime_redesign": True,
}

REQUIRED_STREAMS = (
    "telemetry",
    "assessment_metadata",
    "cli_event",
    "extension_event",
    "ai_usage",
)

REQUIRED_PUBLIC_OR_AUTH_PATHS = (
    "/api/v1/health",
    "/api/v1/telemetry",
    "/api/v1/assessment-metadata",
    "/api/v1/cli-events",
    "/api/v1/extension-events",
    "/api/v1/ai-usage",
    "/api/v1/reports/upload-intents",
    "/api/v1/reports",
    "/api/v1/community/status",
)

FORBIDDEN_18_2_PACKAGES = (
    "verification/community_transparency_prose",
    "verification/community_transparency_publication",
    "verification/community_slice_18_2",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "openai_owner_credential_required",
        "openrouter_owner_credential_required",
        "formal_prose_publication_deferred",
        "marketplace_content_not_published",
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "extension_event_contract_only",
        "ai_usage_assess_path_deferred",
        "api_route_register_stale_vs_runtime",
        "codestrata_ai_favicon_stale_must_fix_before_release",
        "github_v0_1_0_release_expected_gap",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv181Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_18_1: bool = True
    start_slice_18_2: bool = False


def default_contract() -> Sv181Contract:
    return Sv181Contract()
