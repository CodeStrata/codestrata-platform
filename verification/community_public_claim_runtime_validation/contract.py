"""Contract for Slice 18.7 — Validate Public Claims Against Runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-public-claim-runtime-validation-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-public-claim-runtime-validation-verification"
VERSION = "1.0.0"
SUITE_ID = "sv18-7"
SV187_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv18-7"
REPORT_JSON = "community-public-claim-runtime-validation-verification.json"
REPORT_MD = "community-public-claim-runtime-validation-verification.md"

POLICY_RELATIVE = (
    "platform/policies/community_public_claim_runtime_validation_policy.json"
)
CONTRACT_RELATIVE = (
    "platform/contracts/community_public_claim_runtime_validation_verification.json"
)
CLAIM_REGISTER_RELATIVE = (
    "platform/policies/community_public_claim_runtime_validation_register.json"
)
WORKFLOW_REGISTER_RELATIVE = "platform/policies/platform_workflow_authority_register.json"
CONTRADICTION_REGISTER_RELATIVE = (
    "platform/policies/community_transparency_contradiction_register.json"
)
FIELD_REGISTER_RELATIVE = "platform/policies/community_telemetry_field_register.json"
STREAM_REGISTER_RELATIVE = (
    "platform/policies/community_telemetry_stream_inventory_register.json"
)
ROUTE_REGISTER_RELATIVE = "platform/policies/community_api_route_register.json"
TRANSPARENCY_ROUTE_REGISTER_RELATIVE = (
    "platform/policies/community_api_transparency_register.json"
)
TERMINOLOGY_REGISTER_RELATIVE = (
    "platform/policies/community_product_terminology_register.json"
)
RETENTION_REGISTER_RELATIVE = "platform/policies/community_retention_register.json"
AI_FLOW_REGISTER_RELATIVE = (
    "platform/policies/community_ai_provider_data_flow_register.json"
)
SOURCE_LOCALITY_REGISTER_RELATIVE = (
    "platform/policies/community_source_locality_register.json"
)
HEADS_PY = "engine/src/codestrata/artifacts/heads.py"
LANDING_PY = "engine/src/codestrata/cli/landing.py"
COLLECTED_FIELDS_DOC = "docs/security/collected-fields.md"
DATA_COLLECTION_DOC = "docs/security/data-collection.md"
SOURCE_LOCALITY_DOC = "docs/security/source-locality.md"
COMMUNITY_API_DOC = "docs/reference/community-api/index.md"
AI_PROVIDERS_DOC = "docs/ai-providers/index.md"
CLI_DOC = "docs/reference/cli.md"
ENGINE_README = "engine/README.md"
ENGINE_PRIVACY = "engine/PRIVACY.md"
ENGINE_SECURITY = "engine/SECURITY.md"
ROOT_README = "README.md"
ROOT_SECURITY = "SECURITY.md"
VSCODE_README = "vscode-plugin/README.md"
VSCODE_PACKAGE = "vscode-plugin/package.json"
REPORTS_LANDING = "reports/public/index.html"
PYPROJECT = "engine/pyproject.toml"

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "all_material_public_claims_inventoried": True,
    "all_claims_runtime_evidenced": True,
    "unsupported_claims_forbidden": True,
    "telemetry_producer_status_honest": True,
    "ai_provider_status_honest": True,
    "source_locality_claims_validated": True,
    "retention_claims_validated": True,
    "report_publish_claims_validated": True,
    "cli_claims_validated": True,
    "vscode_claims_validated": True,
    "api_routes_validated": True,
    "contradictions_classified": True,
    "release_dispositions_explicit": True,
    "start_slice_18_7": True,
    "start_slice_18_8": False,
    "no_cli_publish": True,
    "no_vscode_marketplace_publish": True,
    "no_release_tag": True,
    "no_full_22_repository_release_corpus": True,
    "no_product_capability_redesign": True,
    "no_runtime_redesign": True,
    "no_telemetry_schema_change": True,
    "no_community_api_redesign": True,
}

FORBIDDEN_18_8_PACKAGES = (
    "verification/community_slice_18_8",
    "verification/community_release_readiness",
    "verification/community_release_readiness_publication",
    "verification/community_public_transparency_publication",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "github_release_still_0_1_0",
        "marketplace_content_not_published",
        "website_favicon_deferred",
        "openai_owner_credential_required",
        "openrouter_owner_credential_required",
        "deferred_telemetry_producers",
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "full_release_corpus_deferred",
        "live_endpoint_soft_probe",
        "known_public_report_probe_deferred",
    }
)

LIVE_ENDPOINTS: tuple[tuple[str, int], ...] = (
    ("https://docs.codestrata.ai/security/data-collection/", 200),
    ("https://docs.codestrata.ai/security/privacy/", 200),
    ("https://docs.codestrata.ai/security/source-locality/", 200),
    ("https://docs.codestrata.ai/security/retention-and-deletion/", 200),
    ("https://docs.codestrata.ai/security/collected-fields/", 200),
    ("https://docs.codestrata.ai/architecture/community-cloud/", 200),
    ("https://docs.codestrata.ai/reference/community-api/", 200),
    ("https://api.codestrata.ai/api/v1/health", 200),
    ("https://api.codestrata.ai/api/v1/community/status", 200),
    ("https://reports.codestrata.ai/", 200),
    ("https://reports.codestrata.ai/r/does-not-exist-sv18-7", 404),
    ("https://insights.codestrata.ai/", 200),
)

ALLOWED_CLAIM_STATUSES = frozenset(
    {
        "SUPPORTED",
        "SUPPORTED_WITH_QUALIFICATION",
        "STALE",
        "UNSUPPORTED",
        "CONTRADICTORY",
        "EXPECTED_RELEASE_GAP",
    }
)

ALLOWED_RELEASE_DISPOSITIONS = frozenset(
    {
        "NONE",
        "RELEASE_BLOCKER",
        "MUST_FIX_BEFORE_RELEASE",
        "DOCUMENTATION_FIX_NOW",
        "EXPECTED_RELEASE_GAP",
        "POST_RELEASE_ACCEPTABLE",
        "RELEASE_CARRY_FORWARD",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv187Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_18_7: bool = True
    start_slice_18_8: bool = False


def default_contract() -> Sv187Contract:
    return Sv187Contract()
