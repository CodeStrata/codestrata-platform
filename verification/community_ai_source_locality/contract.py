"""Contract for Slice 18.4 — AI Provider + Source-Locality Transparency."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-ai-source-locality-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-ai-source-locality-verification"
VERSION = "1.0.0"
SUITE_ID = "sv18-4"
SV184_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv18-4"
REPORT_JSON = "community-ai-source-locality-verification.json"
REPORT_MD = "community-ai-source-locality-verification.md"

POLICY_RELATIVE = "platform/policies/community_ai_source_locality_transparency_policy.json"
CONTRACT_RELATIVE = "platform/contracts/community_ai_source_locality_verification.json"
WORKFLOW_REGISTER_RELATIVE = "platform/policies/platform_workflow_authority_register.json"
AI_FLOW_REGISTER_RELATIVE = "platform/policies/community_ai_provider_data_flow_register.json"
SOURCE_LOCALITY_REGISTER_RELATIVE = (
    "platform/policies/community_source_locality_register.json"
)
CLAIM_REGISTER_RELATIVE = (
    "platform/policies/community_ai_source_locality_claim_register.json"
)

SOURCE_LOCALITY_DOC = "docs/security/source-locality.md"
AI_PROVIDERS_DOC = "docs/ai-providers/index.md"
PRIVACY_DOC = "docs/security/privacy.md"
TELEMETRY_DOC = "docs/reference/telemetry.md"
DATA_COLLECTION_DOC = "docs/security/data-collection.md"
COMMUNITY_API_DOC = "docs/reference/community-api/index.md"
CLI_DOC = "docs/reference/cli.md"
VSCODE_DOC = "docs/extensions/vscode.md"
ENGINE_PRIVACY = "engine/PRIVACY.md"
VSCODE_PRIVACY = "vscode-plugin/PRIVACY.md"

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "ai_optional_documented": True,
    "no_ai_mode_documented": True,
    "provider_data_flow_documented": True,
    "provider_specific_status_documented": True,
    "bedrock_live_e2e_documented": True,
    "openai_owner_prerequisite_documented": True,
    "openrouter_owner_prerequisite_documented": True,
    "deterministic_assessment_provider_independent_documented": True,
    "provider_failure_non_blocking_documented": True,
    "provider_credentials_not_telemetry_documented": True,
    "prompts_responses_not_community_telemetry_documented": True,
    "third_party_retention_not_speculated": True,
    "eir_ai_boundary_documented": True,
    "source_locality_matrix_published": True,
    "start_slice_18_4": True,
    "start_slice_18_5": False,
    "no_cli_publish": True,
    "no_vscode_marketplace_publish": True,
    "no_release_tag": True,
    "no_full_22_repository_release_corpus": True,
    "no_ai_runtime_redesign": True,
    "no_new_provider_features": True,
    "no_telemetry_schema_changes": True,
}

FORBIDDEN_18_5_PACKAGES = (
    "verification/community_public_transparency_publication",
    "verification/community_slice_18_5",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "openai_owner_credential_required",
        "openrouter_owner_credential_required",
        "third_party_ai_retention_governed_externally",
        "vscode_provider_selection_ui_deferred",
        "marketplace_content_not_published",
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "live_docs_unreachable",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv184Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_18_4: bool = True
    start_slice_18_5: bool = False


def default_contract() -> Sv184Contract:
    return Sv184Contract()
