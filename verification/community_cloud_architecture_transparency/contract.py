"""Contract for Slice 18.5 — Community Cloud Architecture Transparency."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-cloud-architecture-transparency-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-cloud-architecture-transparency-verification"
VERSION = "1.0.0"
SUITE_ID = "sv18-5"
SV185_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv18-5"
REPORT_JSON = "community-cloud-architecture-transparency-verification.json"
REPORT_MD = "community-cloud-architecture-transparency-verification.md"

POLICY_RELATIVE = (
    "platform/policies/community_cloud_architecture_transparency_policy.json"
)
CONTRACT_RELATIVE = (
    "platform/contracts/community_cloud_architecture_transparency_verification.json"
)
WORKFLOW_REGISTER_RELATIVE = "platform/policies/platform_workflow_authority_register.json"
ROUTE_REGISTER_RELATIVE = "platform/policies/community_api_route_register.json"
CONTRADICTION_REGISTER_RELATIVE = (
    "platform/policies/community_transparency_contradiction_register.json"
)
CLAIM_REGISTER_RELATIVE = (
    "platform/policies/community_cloud_architecture_claim_register.json"
)
DOC_AUTHORITY_RELATIVE = (
    "platform/policies/community_documentation_authority_register.json"
)

ARCH_INDEX = "docs/architecture/index.md"
COMMUNITY_CLOUD_DOC = "docs/architecture/community-cloud.md"
DATA_LAKE_DOC = "docs/architecture/data-lake.md"
INSIGHTS_DOC = "docs/architecture/insights.md"
COMMUNITY_API_DOC = "docs/reference/community-api/index.md"
SOURCE_LOCALITY_DOC = "docs/security/source-locality.md"
TELEMETRY_DOC = "docs/reference/telemetry.md"
DATA_COLLECTION_DOC = "docs/security/data-collection.md"
PRIVACY_DOC = "docs/security/privacy.md"
VITEPRESS_CONFIG = "docs/.vitepress/config.ts"
ENGINE_README = "engine/README.md"
ENGINE_PRIVACY = "engine/PRIVACY.md"
ENGINE_SECURITY = "engine/SECURITY.md"
ROOT_SECURITY = "SECURITY.md"

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "api_authority_documented": True,
    "community_routes_documented": True,
    "active_producer_status_honest": True,
    "data_lake_architecture_documented": True,
    "report_store_separate_documented": True,
    "insights_architecture_documented": True,
    "insights_privacy_documented": True,
    "community_status_documented": True,
    "failure_isolation_documented": True,
    "complete_data_flow_diagram_published": True,
    "security_boundaries_documented": True,
    "start_slice_18_5": True,
    "start_slice_18_6": False,
    "no_cli_publish": True,
    "no_vscode_marketplace_publish": True,
    "no_release_tag": True,
    "no_full_22_repository_release_corpus": True,
    "no_runtime_redesign": True,
    "no_telemetry_schema_changes": True,
    "no_data_lake_redesign": True,
    "no_insights_redesign": True,
    "no_community_api_behavior_change": True,
}

FORBIDDEN_18_6_PACKAGES = (
    "verification/community_public_transparency_publication",
    "verification/community_slice_18_6",
    "verification/community_release_readiness_publication",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "deferred_event_producers",
        "marketplace_content_not_published",
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "full_release_corpus_deferred",
        "live_docs_unreachable",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv185Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_18_5: bool = True
    start_slice_18_6: bool = False


def default_contract() -> Sv185Contract:
    return Sv185Contract()
