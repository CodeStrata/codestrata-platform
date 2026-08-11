"""Contract for Slice 18.2 — Telemetry + Data Collection Transparency."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-telemetry-data-transparency-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-telemetry-data-transparency-verification"
VERSION = "1.0.0"
SUITE_ID = "sv18-2"
SV182_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv18-2"
REPORT_JSON = "community-telemetry-data-transparency-verification.json"
REPORT_MD = "community-telemetry-data-transparency-verification.md"

POLICY_RELATIVE = "platform/policies/community_telemetry_data_transparency_policy.json"
POLICY_SCHEMA = "community-telemetry-data-transparency-policy:1.0"
CONTRACT_RELATIVE = (
    "platform/contracts/community_telemetry_data_transparency_verification.json"
)
WORKFLOW_REGISTER_RELATIVE = "platform/policies/platform_workflow_authority_register.json"
CONTRADICTION_REGISTER_RELATIVE = (
    "platform/policies/community_transparency_contradiction_register.json"
)
FIELD_REGISTER_RELATIVE = "platform/policies/community_telemetry_field_register.json"
STREAM_REGISTER_RELATIVE = (
    "platform/policies/community_telemetry_stream_inventory_register.json"
)
CLAIM_REGISTER_RELATIVE = (
    "platform/policies/community_telemetry_data_transparency_claim_register.json"
)

TELEMETRY_DOC = "docs/reference/telemetry.md"
DATA_COLLECTION_DOC = "docs/security/data-collection.md"
COLLECTED_FIELDS_DOC = "docs/security/collected-fields.md"
PRIVACY_DOC = "docs/security/privacy.md"
CLI_DOC = "docs/reference/cli.md"
VSCODE_DOC = "docs/extensions/vscode.md"
ENGINE_PRIVACY = "engine/PRIVACY.md"
VSCODE_PRIVACY = "vscode-plugin/PRIVACY.md"

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "telemetry_disabled_by_default_documented": True,
    "explicit_opt_in_documented": True,
    "explicit_opt_out_documented": True,
    "non_interactive_behavior_documented": True,
    "consent_not_publish_authorization_documented": True,
    "all_collected_fields_documented": True,
    "never_collected_claims_runtime_backed": True,
    "installation_identity_documented": True,
    "production_transport_documented": True,
    "data_lake_boundary_documented": True,
    "report_store_separation_documented": True,
    "telemetry_retention_documented": True,
    "opt_out_scope_documented": True,
    "producer_status_honest": True,
    "public_examples_schema_validated": True,
    "canonical_document_authority_preserved": True,
    "t18_c004_resolved": True,
    "start_slice_18_2": True,
    "start_slice_18_3": False,
    "no_cli_publish": True,
    "no_vscode_marketplace_publish": True,
    "no_release_tag": True,
    "no_full_22_repository_release_corpus": True,
    "no_telemetry_runtime_redesign": True,
    "no_new_event_producers": True,
}

FORBIDDEN_18_3_PACKAGES = (
    "verification/community_retention_deletion_transparency",
    "verification/community_slice_18_3",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "contract_deferred_streams_not_emitted",
        "openai_owner_credential_required",
        "openrouter_owner_credential_required",
        "broader_retention_deletion_deferred_to_18_3",
        "marketplace_content_not_published",
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "live_docs_unreachable",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv182Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_18_2: bool = True
    start_slice_18_3: bool = False


def default_contract() -> Sv182Contract:
    return Sv182Contract()
