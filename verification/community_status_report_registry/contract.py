"""Contract for Slice 17.23 — Community Status + Published Report Registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-status-report-registry-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-status-report-registry-verification"
VERSION = "1.0.0"
SUITE_ID = "sv17-23"
SV1723_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-23"
REPORT_JSON = "community-status-report-registry-verification.json"
REPORT_MD = "community-status-report-registry-verification.md"

POLICY_RELATIVE = "platform/policies/community_status_report_registry_policy.json"
POLICY_SCHEMA = "community-status-report-registry-policy:1.0"
STATUS_REGISTER_RELATIVE = "platform/policies/community_status_register.json"
STATUS_REGISTER_SCHEMA = "community-status-register:1.0"
PUBLISHED_REGISTER_RELATIVE = (
    "platform/policies/community_published_report_validation_register.json"
)
CONTRACT_RELATIVE = "platform/contracts/community_status_report_registry_verification.json"

EXPECTED_17_22_PACKAGE = "verification/community_epic17_defect_resolution"
EXPECTED_17_23_PACKAGE = "verification/community_status_report_registry"

SLICE_17_24_PACKAGE_CANDIDATES = (
    "verification/community_production_slice_17_24",
    "verification/community_release_epic",
    "verification/community_marketplace_publish",
)

PUBLIC_API = "https://api.codestrata.ai"
PUBLIC_STATUS_URL = "https://api.codestrata.ai/api/v1/community/status"
PUBLIC_REPORTS = "https://reports.codestrata.ai"
PUBLIC_REPORTS_PREFIX = "https://reports.codestrata.ai/r/"

PUBLIC_REPORT_URLS_RELATIVE = (
    ".codestrata-artifacts/validation/suites/release-v0.2.0/public-report-urls.json"
)
PUBLIC_REPORT_URLS_SCHEMA = "public-report-urls-manifest:1.1"
FLASK_17_21_REPO_ID = "local-flask"

COMMUNITY_STATUS_DIR = (
    "platform/src/codestrata_platform/community_cloud_api/community_status"
)
COMMUNITY_STATUS_ROUTES = (
    "platform/src/codestrata_platform/community_cloud_api/community_status/routes.py"
)
COMMUNITY_STATUS_GITHUB = (
    "platform/src/codestrata_platform/community_cloud_api/community_status/github_stars.py"
)
COMMUNITY_STATUS_SERVICE = (
    "platform/src/codestrata_platform/community_cloud_api/community_status/service.py"
)
COMMUNITY_CLOUD_APP = "platform/src/codestrata_platform/community_cloud_api/app.py"

ENGINE_PUBLIC_REPORT_URL_MANIFEST = (
    "engine/src/codestrata/community_cloud/public_report_url_manifest.py"
)
ENGINE_INIT = "engine/src/codestrata/__init__.py"

INSIGHTS_PUBLISHED_PAGE = "insights/src/pages/PublishedReportsPage.tsx"
INSIGHTS_APP_SHELL = "insights/src/components/AppShell.tsx"
INSIGHTS_APP = "insights/src/app/App.tsx"
INSIGHTS_AUTH_ROUTES = (
    "platform/src/codestrata_platform/community_cloud_api/insights_auth/routes.py"
)
INSIGHTS_API_PATH = "/insights/api/published-reports"
INSIGHTS_PAGE_ROUTE = "/published-reports"

DOCS_COMMUNITY_API = "docs/reference/community-api/index.md"
SITE_JS_RELATIVE = "assets/site.js"

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "community_status_public_read": True,
    "engine_version_authoritative": True,
    "github_stars_cached": True,
    "github_credentials_browser_exposed": False,
    "public_report_url_manifest_validation_evidence": True,
    "public_report_url_manifest_auto_update": True,
    "report_registry_current_previous_only": True,
    "insights_report_registry_authenticated": True,
    "report_rendering_remains_reports_domain": True,
    "marketplace_publish": False,
    "full_22_repo_release_corpus": False,
    "start_slice_17_23": True,
    "start_slice_17_24": False,
}

SOFT_LIMITATION_CODES = frozenset(
    {
        "full_22_corpus_deferred_to_release",
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "github_temporary_unavailable_handled",
        "website_deploy_owner_follow_up",
        "status_api_deploy_pending",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def sibling_site_root(monorepo: Path) -> Path:
    return monorepo.parent / "codestrata-site"


@dataclass(frozen=True, slots=True)
class Sv1723Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_23: bool = True
    start_slice_17_24: bool = False


def default_contract() -> Sv1723Contract:
    return Sv1723Contract()
