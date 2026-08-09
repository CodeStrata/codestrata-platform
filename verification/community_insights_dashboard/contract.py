"""Contract for Slice 15.10 dashboard verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_insights_dashboard import (
    COMMUNITY_INSIGHTS_DASHBOARD_ID,
    COMMUNITY_INSIGHTS_DASHBOARD_VERSION,
)

SCHEMA_NAME = "community-insights-dashboard-verification"
SCHEMA_VERSION = "1.0.0"
SV1510_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv15-10"
REPORT_JSON = "community-insights-dashboard-verification.json"
REPORT_MD = "community-insights-dashboard-verification.md"

POLICY_ID = "codestrata-insights-dashboard-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/codestrata_insights_dashboard_policy.json"
DASHBOARD_CONTRACT_RELATIVE = (
    "platform/policies/codestrata_insights_dashboard_contract.json"
)

APP_ROOT = "insights"
PACKAGE_JSON = "insights/package.json"

FORBIDDEN_CHART_PACKAGES: tuple[str, ...] = (
    "chart.js",
    "react-chartjs-2",
    "recharts",
    "d3",
    "nivo",
    "echarts",
    "echarts-for-react",
)

DASHBOARD_SOURCE_FILES: tuple[str, ...] = (
    "insights/src/pages/DashboardPage.tsx",
    "insights/src/components/MetricCard.tsx",
    "insights/src/components/charts/DistributionChart.tsx",
    "insights/src/components/DashboardErrorBoundary.tsx",
    "insights/src/dashboard/format.ts",
    "insights/src/dashboard/labels.ts",
    "insights/src/api/insightsApi.ts",
    "insights/src/api/authClient.ts",
    "insights/src/api/syntheticMocks.ts",
    "insights/src/app/App.tsx",
    "insights/index.html",
    "insights/package.json",
)

PRIVACY_UI_FILES: tuple[str, ...] = (
    "insights/src/pages/DashboardPage.tsx",
    "insights/src/components/MetricCard.tsx",
    "insights/src/components/charts/DistributionChart.tsx",
    "insights/src/dashboard/format.ts",
    "insights/src/dashboard/labels.ts",
    "insights/src/api/syntheticMocks.ts",
)

PRIVACY_FORBIDDEN_FIELDS: tuple[str, ...] = (
    "installation_id",
    "event_id",
    "s3_key",
    "model_id",
    "repository_name",
    "file_path",
    "source_code",
    "prompt",
    "credential",
)

FORBIDDEN_15_12_PATHS: tuple[str, ...] = (
    ".codestrata-artifacts/validation/suites/sv17-1",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "production_deployment_disabled",
        "production_ingestion_still_unwired",
        "no_live_dashboard_data_claim",
        "validation_growth_snapshots_unavailable",
        "worktree_uncommitted",
        "browser_screenshot_tooling_may_be_unavailable",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1510Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_INSIGHTS_DASHBOARD_ID
    package_version: str = COMMUNITY_INSIGHTS_DASHBOARD_VERSION
    start_slice_15_12: bool = False
    production_deployment_enabled: bool = False
    production_ingestion_enabled: bool = False
    no_deploy: bool = True
    no_commit: bool = True


def default_contract() -> Sv1510Contract:
    return Sv1510Contract()
