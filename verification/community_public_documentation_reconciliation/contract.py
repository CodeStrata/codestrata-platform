"""Contract for Slice 17.26 — Community public documentation reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-public-documentation-reconciliation-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-public-documentation-reconciliation-verification"
VERSION = "1.0.0"
SUITE_ID = "sv17-26"
SV1726_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-26"
REPORT_JSON = "community-public-documentation-reconciliation-verification.json"
REPORT_MD = "community-public-documentation-reconciliation-verification.md"

POLICY_RELATIVE = (
    "platform/policies/community_public_documentation_reconciliation_policy.json"
)
POLICY_SCHEMA = "community-public-documentation-reconciliation-policy:1.0"
CONTRACT_RELATIVE = (
    "platform/contracts/community_public_documentation_reconciliation_verification.json"
)
WORKFLOW_REGISTER_RELATIVE = "platform/policies/platform_workflow_authority_register.json"

PRIVACY_DOC_RELATIVE = "docs/security/privacy.md"
ENGINE_PRIVACY_RELATIVE = "engine/PRIVACY.md"
CS_FOOTER_RELATIVE = "docs/.vitepress/theme/CsFooter.vue"
REPORTS_INDEX_RELATIVE = "reports/public/index.html"
REPORTS_FAVICON_ICO = "reports/public/favicon.ico"
REPORTS_FAVICON_PNG = "reports/public/favicon.png"
REPORTS_APPLE_TOUCH = "reports/public/apple-touch-icon.png"
GITIGNORE_RELATIVE = ".gitignore"

CANONICAL_COMMUNITY_PRIVACY_URL = "https://docs.codestrata.ai/security/privacy"
CORPORATE_PRIVACY_URL = "https://codestrata.ai/privacy"
LIVE_DOCS_PRIVACY_URL = CANONICAL_COMMUNITY_PRIVACY_URL
LIVE_REPORTS_FAVICON_URL = "https://reports.codestrata.ai/favicon.ico"
LIVE_REPORTS_LANDING_URL = "https://reports.codestrata.ai/"
LIVE_CORPORATE_HOME_URL = "https://codestrata.ai/"

PRIVACY_SECTION_MARKERS = (
    "Local assessment",
    "Telemetry",
    "Never collected",
    "Data Lake",
    "Published reports",
    "AI providers",
    "Retention",
    "Opt-out",
)

# Legacy published-report filesystem path that must not appear in docs markdown.
STALE_REPORT_PATH_LITERAL = "reports/<repo>/<timestamp>/report.html"
STALE_REPORT_PATH_RE = r"reports/[A-Za-z0-9._-]+/\d{4,}[^/\s]*/report\.html"

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "slice": "17.26",
    "start_slice_17_26": True,
    "start_slice_17_27": False,
    "no_cli_publish": True,
    "no_vscode_marketplace_publish": True,
    "no_release_tag": True,
    "no_full_22_repository_release_corpus": True,
    "canonical_community_privacy_url": CANONICAL_COMMUNITY_PRIVACY_URL,
    "corporate_privacy_url": CORPORATE_PRIVACY_URL,
    "reports_privacy_must_point_to_community_docs": True,
}

SOFT_LIMITATION_CODES = frozenset(
    {
        "live_docs_privacy_unreachable",
        "live_reports_favicon_unreachable",
        "live_reports_landing_privacy_mismatch",
        "codestrata_ai_favicon_stale",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1726Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_26: bool = True
    start_slice_17_27: bool = False


def default_contract() -> Sv1726Contract:
    return Sv1726Contract()
