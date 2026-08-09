"""Contract for Slice 17.11."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_production_site_ux_access import (
    COMMUNITY_PRODUCTION_SITE_UX_ACCESS_ID,
    VERSION,
)

SCHEMA_NAME = "community-production-site-ux-access-verification"
SCHEMA_VERSION = "1.0.0"
SV1711_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-11"
REPORT_JSON = "community-production-site-ux-access-verification.json"
REPORT_MD = "community-production-site-ux-access-verification.md"

POLICY_RELATIVE = "platform/policies/community_production_site_ux_access_policy.json"
POLICY_SCHEMA = "community-production-site-ux-access-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_production_site_ux_access_register.json"
REGISTER_SCHEMA = "community-production-site-ux-access-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_production_site_ux_access_verification.json"
INSIGHTS_POLICY_RELATIVE = "insights/policies/community_production_site_ux_access_policy.json"
INSIGHTS_REGISTER_RELATIVE = "insights/policies/community_production_site_ux_access_register.json"

SITES_POLICY_RELATIVE = "platform/policies/community_production_sites_repository_deployment_policy.json"

EVIDENCE_DIR_RELATIVE = "infrastructure/production/.local/sv17-11"
EVIDENCE_FILES = (
    "password-rca.json",
    "live-auth.json",
    "live-docs.json",
    "github-visibility.json",
    "deploy.json",
)

DOCS_CONFIG = "docs/.vitepress/config.ts"
DOCS_CUSTOM_CSS = "docs/.vitepress/theme/custom.css"
DOCS_FOOTER = "docs/.vitepress/theme/CsFooter.vue"
DOCS_HOME_LINK = "docs/.vitepress/theme/CsDocsHomeLink.vue"
DOCS_FAVICON = "docs/public/favicon.svg"
DESIGN_SYSTEM_FAVICON = "design-system/assets/brand/codestrata-mark-on-dark.svg"

INSIGHTS_INDEX = "insights/index.html"
INSIGHTS_FAVICON = "insights/public/brand/codestrata-mark-on-dark.svg"
INSIGHTS_LOGIN_PAGE = "insights/src/pages/LoginPage.tsx"
INSIGHTS_AUTH_CONTEXT = "insights/src/auth/AuthContext.tsx"

EXPECTED_REGION = "us-west-2"
EXPECTED_ENVIRONMENT = "production"
EXPECTED_AUTH_ROOT_CAUSE = "sm_stores_scrypt_verifier_owner_must_use_plaintext_owner_once"
EXPECTED_DOCS_LOGO_DESTINATION = "/"
EXPECTED_DOCS_MAIN_SITE = "https://codestrata.ai/"
EXPECTED_DOCS_INNER_FOOTER = "minimal/legal-only on inner pages"
EXPECTED_FAVICON_STATUS = "approved dark-theme mark"

PRIOR_VERIFICATION_PACKAGES = (
    "verification/community_production_sites_deployment",
    "verification/community_cloud_incremental_deployment",
    "verification/community_cloud_production_recovery",
)

SLICE_17_12_POLICY_CANDIDATES = (
    "platform/policies/community_cloud_slice_17_13_policy.json",
    "platform/policies/community_production_slice_17_13_policy.json",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "owner_once_password_file_manual_copy_delete",
        "monorepo_remains_source_authority_pre_cutover",
        "query_budget_reached_preexisting",
        "worktree_uncommitted",
        "github_cli_auth_pending",
        "live_auth_evidence_absent",
        "live_docs_evidence_absent",
        "github_visibility_evidence_absent",
        "deploy_evidence_absent",
        "password_rca_evidence_absent",
    }
)

REGISTER_FIELDS = (
    "docs_repo_visibility",
    "docs_site_public",
    "docs_header_overlap_fixed",
    "docs_logo_destination",
    "docs_main_site_destination",
    "docs_inner_footer_posture",
    "docs_favicon_status",
    "insights_favicon_status",
    "insights_auth_root_cause",
    "insights_password_rotation_performed",
    "insights_login_status",
    "production_sites_status",
    "start_slice_17_11",
    "start_slice_17_12",
)

SOFT_CHECK_IDS = frozenset(
    {
        "operational:live_auth",
        "operational:live_docs",
        "operational:github_visibility",
        "operational:deploy",
        "auth:password_rca_evidence",
        "regression:prior_packages",
        "insights:login_page_soft",
        "insights:auth_context_soft",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1711Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_PRODUCTION_SITE_UX_ACCESS_ID
    package_version: str = VERSION
    start_slice_17_11: bool = True
    start_slice_17_12: bool = True
    start_slice_17_13: bool = False
    docs_repo_visibility: str = "private"
    docs_site_public: bool = True
    docs_header_overlap_fixed: bool = True
    docs_logo_destination: str = EXPECTED_DOCS_LOGO_DESTINATION
    docs_main_site_destination: str = EXPECTED_DOCS_MAIN_SITE
    docs_inner_footer_posture: str = EXPECTED_DOCS_INNER_FOOTER
    docs_favicon_status: str = EXPECTED_FAVICON_STATUS
    insights_favicon_status: str = EXPECTED_FAVICON_STATUS
    insights_auth_root_cause: str = EXPECTED_AUTH_ROOT_CAUSE
    insights_password_rotation_performed: bool = False
    insights_login_status: str = "owner_once_plaintext_required"
    production_sites_status: str = "cloudflare_live_private_repos_public_sites"
    region: str = EXPECTED_REGION
    environment: str = EXPECTED_ENVIRONMENT


def default_contract() -> Sv1711Contract:
    return Sv1711Contract()
