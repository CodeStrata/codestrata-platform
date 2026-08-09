"""Contract for Slice 14.2 community documentation redesign verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_documentation_redesign import (
    COMMUNITY_DOCS_REDESIGN_ID,
    COMMUNITY_DOCS_REDESIGN_VERSION,
)

SCHEMA_NAME = "community-documentation-redesign-verification"
SCHEMA_VERSION = "1.0.0"
SV142_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv14-2"
REPORT_JSON = "community-documentation-redesign-verification.json"
REPORT_MD = "community-documentation-redesign-verification.md"

POLICY_ID = "community-documentation-redesign-policy"
POLICY_VERSION = "1.0"
DOCS_ROOT = "docs"
DESIGN_SYSTEM_TOKENS = "design-system/tokens/tokens.css"

REQUIRED_COMMUNITY_ROUTES = (
    "getting-started/",
    "getting-started/install",
    "getting-started/repository-initialization",
    "reference/cli",
    "extensions/vscode",
    "ai-providers/",
    "assessments/",
    "reports/",
    "reports/engineering-intelligence",
    "reference/configuration",
    "security/privacy",
    "reference/telemetry",
    "reference/api",
    "troubleshooting/",
    "faq/",
    "reference/release-notes",
)

FORBIDDEN_NAV_FRAGMENTS = (
    'link: "/platform/"',
    'text: "Platform"',
    'link: "/community/vs-platform"',
)

FORBIDDEN_14_8_PATHS = (
    "verification/chart_standardization",
    "verification/score_risk_visualization",
    "design-system/applications/charts",
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "visual_baselines_may_need_refresh",
        "full_axe_ci_optional",
        "slice_14_3_not_started",
        "slice_14_8_not_started",
        "worktree_uncommitted",
        "theme_validate_requires_preview_server",
        "historical_platform_md_retained_excluded",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv142Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_DOCS_REDESIGN_ID
    package_version: str = COMMUNITY_DOCS_REDESIGN_VERSION
    start_slice_14_3: bool = False
    no_assessment_html_redesign: bool = True
    no_eir_redesign: bool = True
    no_vscode_redesign: bool = True
    no_marketplace_redesign: bool = True
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv142Contract:
    return Sv142Contract()
