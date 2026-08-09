"""Contract for Slice 15.11 validation verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_insights_validation import (
    COMMUNITY_INSIGHTS_VALIDATION_ID,
    COMMUNITY_INSIGHTS_VALIDATION_VERSION,
)

SCHEMA_NAME = "community-insights-validation-verification"
SCHEMA_VERSION = "1.0.0"
SV1511_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv15-11"
REPORT_JSON = "community-insights-validation-verification.json"
REPORT_MD = "community-insights-validation-verification.md"

POLICY_ID = "community-insights-validation-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/community_insights_validation_policy.json"
VALIDATION_CONTRACT_RELATIVE = (
    "platform/policies/community_insights_validation_contract.json"
)

APP_ROOT = "insights"
PACKAGE_JSON = "insights/package.json"
INFRA_MODULE = "infrastructure/modules/community-insights-auth"

INSIGHTS_PACKAGES: tuple[str, ...] = (
    "platform/src/codestrata_platform/community_cloud_api/insights",
    "platform/src/codestrata_platform/community_cloud_api/insights_auth",
    "platform/src/codestrata_platform/community_cloud_api/insights_storage",
    "platform/src/codestrata_platform/community_cloud_api/insights_query",
)

PRIOR_SLICE_PACKAGES: tuple[tuple[str, str], ...] = (
    ("sv15-1", "verification/community_data_lake_audit"),
    ("sv15-2", "verification/community_analytics_partition"),
    ("sv15-3", "verification/community_insights_event_coverage"),
    ("sv15-4", "verification/community_insights_ingestion"),
    ("sv15-5", "verification/community_insights_query_strategy"),
    ("sv15-6", "verification/community_insights_metrics"),
    ("sv15-7", "verification/community_insights_aggregation"),
    ("sv15-8", "verification/community_insights_application"),
    ("sv15-9", "verification/community_insights_auth"),
    ("sv15-10", "verification/community_insights_dashboard"),
)

FORBIDDEN_CHART_PACKAGES: tuple[str, ...] = (
    "chart.js",
    "react-chartjs-2",
    "recharts",
    "d3",
    "nivo",
    "echarts",
    "echarts-for-react",
)

PRIVACY_UI_FILES: tuple[str, ...] = (
    "insights/src/pages/DashboardPage.tsx",
    "insights/src/components/MetricCard.tsx",
    "insights/src/components/charts/DistributionChart.tsx",
    "insights/src/dashboard/format.ts",
    "insights/src/dashboard/labels.ts",
    "insights/src/api/syntheticMocks.ts",
)

FRONTEND_SOURCE_FILES: tuple[str, ...] = (
    *PRIVACY_UI_FILES,
    "insights/src/api/insightsApi.ts",
    "insights/src/api/authClient.ts",
    "insights/src/app/App.tsx",
    "insights/index.html",
    "insights/package.json",
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

ALLOWED_PRIOR_REPORT_DIRS: frozenset[str] = frozenset(
    {
        "sv15-1",
        "sv15-2",
        "sv15-3",
        "sv15-4",
        "sv15-5",
        "sv15-6",
        "sv15-7",
        "sv15-8",
        "sv15-9",
        "sv15-10",
        "sv15-11",
        "sv15-12",
    }
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "no_live_production_data",
        "retention_only_first_repeat_history",
        "optional_installation_id_undercount",
        "validation_growth_snapshots_unavailable",
        "no_formal_wcag_certification",
        "no_real_aws_secrets_manager_integration",
        "one_browser_os",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1511Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_INSIGHTS_VALIDATION_ID
    package_version: str = COMMUNITY_INSIGHTS_VALIDATION_VERSION
    start_epic_16: bool = False
    production_deployment_enabled: bool = False
    production_ingestion_enabled: bool = False
    live_dashboard_data_available: bool = False
    no_deploy: bool = True
    no_commit: bool = True
    aws_called: bool = False


def default_contract() -> Sv1511Contract:
    return Sv1511Contract()
