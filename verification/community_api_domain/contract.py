"""Contract for Slice 17.14."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-api-domain-verification"
SCHEMA_VERSION = "1.0.0"
SUITE_ID = "sv17-14"
SV1714_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-14"
REPORT_JSON = "community-api-domain-verification.json"
REPORT_MD = "community-api-domain-verification.md"

POLICY_RELATIVE = "platform/policies/community_api_domain_policy.json"
POLICY_SCHEMA = "community-api-domain-policy:1.0"
DOMAIN_REGISTER_RELATIVE = "platform/policies/community_api_domain_register.json"
DOMAIN_REGISTER_SCHEMA = "community-api-domain-register:1.0"
ROUTE_REGISTER_RELATIVE = "platform/policies/community_api_route_register.json"
ROUTE_REGISTER_SCHEMA = "community-api-route-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_api_domain_verification.json"

PUBLIC_API_BASE = "https://api.codestrata.ai"
PUBLIC_API_HOST = "api.codestrata.ai"
DOCS_PATH = "/reference/community-api/"
DOCS_PAGE_RELATIVE = "docs/reference/community-api/index.md"
DOCS_VITEPRESS_CONFIG = "docs/.vitepress/config.ts"
INSIGHTS_WRANGLER = "insights/wrangler.jsonc"
INSIGHTS_API_PROXY = "insights/workers/api-proxy.ts"
INSIGHTS_AUTH_CLIENT = "insights/src/api/authClient.ts"

PLATFORM_PUBLIC_API_AUTHORITY = (
    "platform/src/codestrata_platform/community_cloud_api/public_api_authority.py"
)
ENGINE_PUBLIC_API_AUTHORITY = "engine/src/codestrata/community_cloud/public_api_authority.py"
VSCODE_PUBLIC_API_AUTHORITY = "vscode-plugin/src/communityCloud/publicApiAuthority.ts"

CUSTOM_DOMAIN_TF = "infrastructure/modules/community-cloud-api/custom_domain.tf"
PRODUCTION_MAIN_TF = "infrastructure/production/main.tf"
PLATFORM_CONSTANTS = "platform/src/codestrata_platform/community_cloud_api/constants.py"

ROUTE_CLASSIFICATIONS = frozenset(
    {"PUBLIC_COMMUNITY", "PRIVATE_INSIGHTS", "INTERNAL_OPERATIONAL", "DEPRECATED"}
)

PRIOR_POLICY_PATHS = (
    "platform/policies/community_cloud_remote_state_policy.json",
    "platform/policies/community_cloud_incremental_deployment_policy.json",
    "platform/policies/community_production_sites_repository_deployment_policy.json",
    "platform/policies/community_22_repository_validation_policy.json",
)

PRIOR_VERIFICATION_PACKAGES = (
    "verification/community_cloud_remote_state",
    "verification/community_cloud_incremental_deployment",
    "verification/community_production_sites_deployment",
    "verification/community_22_repository_validation",
)

SLICE_17_15_PACKAGE_CANDIDATES = (
    "verification/community_api_domain_17_15",
    "verification/community_api_cutover",
    "verification/community_production_slice_17_15",
)

PROHIBITED_DOC_PAYLOAD_KEYS = frozenset(
    {
        "source_code",
        "source",
        "repository_contents",
        "file_path",
        "file_paths",
        "findings",
        "evidence",
        "prompt",
        "prompts",
        "response",
        "responses",
        "api_key",
        "api_keys",
        "machineId",
        "machine_id",
    }
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "execute_api_fallback_retained_intentionally",
        "dns_propagation_or_cache_delay",
        "monorepo_pre_cutover_source_authority",
        "worktree_uncommitted",
        "owner_acm_iam_attach_required",
        "cloudflare_dns_token_required",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1714Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_14: bool = True
    start_slice_17_15: bool = False
    public_api_base: str = PUBLIC_API_BASE


def default_contract() -> Sv1714Contract:
    return Sv1714Contract()
