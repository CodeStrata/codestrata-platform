"""Contract for Slice 17.8."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_production_sites_deployment import (
    COMMUNITY_PRODUCTION_SITES_DEPLOYMENT_ID,
    VERSION,
)

SCHEMA_NAME = "community-production-sites-deployment-verification"
SCHEMA_VERSION = "1.0.0"
SV178_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-8"
REPORT_JSON = "community-production-sites-deployment-verification.json"
REPORT_MD = "community-production-sites-deployment-verification.md"

POLICY_RELATIVE = "platform/policies/community_production_sites_repository_deployment_policy.json"
POLICY_SCHEMA = "community-production-sites-repository-deployment-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_production_repository_register.json"
REGISTER_SCHEMA = "community-production-repository-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_production_sites_deployment_verification.json"
INSIGHTS_POLICY_RELATIVE = "insights/policies/community_production_sites_repository_deployment_policy.json"
OIDC_TRUST_POLICY_RELATIVE = "platform/policies/codestrata_github_oidc_trust_policy.json"
RESIDENCY_MAP_RELATIVE = "platform/policies/repository_residency_map.json"

EXPORT_ROUTER = "scripts/export_repository.py"
EXPORT_ROUTER_PACKAGE = "scripts/repository_export_router"
DOCS_EXPORT_SCRIPT = "scripts/export-public-repos.py"
INFRASTRUCTURE_EXPORT_CMD = (
    "python scripts/export_repository.py --target infrastructure --destination <dir>"
)
INSIGHTS_EXPORT_CMD = "python scripts/export_repository.py --target insights --destination <dir>"
DOCS_EXPORT_CMD = "python scripts/export-public-repos.py --repo codestrata-docs"

LOCAL_DIR_RELATIVE = "infrastructure/production/.local"
LOCAL_EVIDENCE_GLOB = "sv17-8-*.json"

MONOREPO_DIRS = ("infrastructure", "insights", "docs")
INSIGHTS_WRANGLER = "insights/wrangler.jsonc"
DOCS_WRANGLER = "docs/wrangler.jsonc"

EXPECTED_REGION = "us-west-2"
EXPECTED_ENVIRONMENT = "production"
EXPECTED_OWNER = "CodeStrata"

EXPECTED_REPOS = (
    {"owner": "CodeStrata", "name": "codestrata-infrastructure", "visibility": "private"},
    {"owner": "CodeStrata", "name": "codestrata-insights", "visibility": "private"},
    {"owner": "CodeStrata", "name": "codestrata-docs", "visibility": "private"},
)

OIDC_TRANSITIONAL_SUBJECTS = (
    "repo:CodeStrata/codestrata-platform:environment:production",
    "repo:CodeStrata/codestrata-infrastructure:environment:production",
)
OIDC_FINAL_SUBJECT = "repo:CodeStrata/codestrata-infrastructure:environment:production"
OIDC_WILDCARD_FORBIDDEN = "repo:CodeStrata/*"

EXPORT_TARGETS = ("community", "infrastructure", "insights")

SOFT_LIMITATION_CODES = frozenset(
    {
        "monorepo_remains_source_authority_pre_cutover",
        "github_environment_or_cloudflare_owner_configuration_pending",
        "github_workflow_execution_pending",
        "synthetic_only_insights_data",
        "worktree_uncommitted",
        "cloudflare_operator_login_required",
        "insights_dns_pending",
        "live_auth_validation_pending",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv178Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_PRODUCTION_SITES_DEPLOYMENT_ID
    package_version: str = VERSION
    start_slice_17_8: bool = True
    start_slice_17_9: bool = True
    start_slice_17_10: bool = True
    start_slice_17_11: bool = True
    start_slice_17_12: bool = True
    start_slice_17_13: bool = False
    region: str = EXPECTED_REGION
    environment: str = EXPECTED_ENVIRONMENT


def default_contract() -> Sv178Contract:
    return Sv178Contract()
