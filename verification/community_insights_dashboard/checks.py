"""Checks for Slice 15.10 dashboard verification."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_dashboard.contract import (
    APP_ROOT,
    DASHBOARD_CONTRACT_RELATIVE,
    FORBIDDEN_15_12_PATHS,
    FORBIDDEN_CHART_PACKAGES,
    PACKAGE_JSON,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    PRIVACY_FORBIDDEN_FIELDS,
    PRIVACY_UI_FILES,
)
from verification.community_insights_dashboard.inventory import (
    dashboard_source_blob,
    exists,
    load_json,
    read_text,
)
from verification.community_insights_dashboard.models import CheckResult, Defect
from verification.community_insights_dashboard.scenario_checks import check_scenarios


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "dashboard_defect",
) -> None:
    checks.append(CheckResult(name, ok, detail, category))
    if not ok:
        defects.append(Defect(classification, category, "pass", detail))


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)

    _add(checks, defects, "policy:present", bool(policy), "present", "policy")
    _add(
        checks,
        defects,
        "policy:id",
        policy.get("policy_id") == POLICY_ID,
        str(policy.get("policy_id")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:version",
        policy.get("policy_version") == POLICY_VERSION,
        str(policy.get("policy_version")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:slice",
        policy.get("slice") == "15.10",
        str(policy.get("slice")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:ui_must_not_compute_metrics",
        policy.get("ui_must_not_compute_metrics") is True,
        str(policy.get("ui_must_not_compute_metrics")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:chart_library_local_css_svg",
        policy.get("chart_library") == "local_css_svg",
        str(policy.get("chart_library")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:chart_js_allowed_false",
        policy.get("chart_js_allowed") is False,
        str(policy.get("chart_js_allowed")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:chart_cdn_allowed_false",
        policy.get("chart_cdn_allowed") is False,
        str(policy.get("chart_cdn_allowed")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:fake_time_series_forbidden",
        policy.get("fake_time_series_forbidden") is True,
        str(policy.get("fake_time_series_forbidden")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:fabricated_validation_growth_forbidden",
        policy.get("fabricated_validation_growth_forbidden") is True,
        str(policy.get("fabricated_validation_growth_forbidden")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:overview_batch_preferred",
        policy.get("overview_batch_preferred") is True,
        str(policy.get("overview_batch_preferred")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:polling_forbidden",
        policy.get("polling_forbidden") is True,
        str(policy.get("polling_forbidden")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_3_false",
        policy.get("start_slice_16_3", False) is False,
        str(policy.get("start_slice_16_3", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:production_deployment_disabled",
        policy.get("production_deployment_enabled") is False,
        str(policy.get("production_deployment_enabled")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:production_ingestion_disabled",
        policy.get("production_ingestion_enabled") is False,
        str(policy.get("production_ingestion_enabled")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:ai_model_family_display_name",
        policy.get("ai_model_family_display_name") == "AI model family adoption",
        str(policy.get("ai_model_family_display_name")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:validation_dataset_display_name",
        policy.get("validation_dataset_display_name") == "Validation dataset size",
        str(policy.get("validation_dataset_display_name")),
        "policy",
    )
    display = policy.get("display_names") or {}
    _add(
        checks,
        defects,
        "policy:anonymous_installations_label",
        display.get("total_anonymous_installations") == "Anonymous installations",
        str(display.get("total_anonymous_installations")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:validation_growth_label_is_size",
        display.get("validation_dataset_growth") == "Validation dataset size",
        str(display.get("validation_dataset_growth")),
        "policy",
    )
    return checks, defects


def check_contract(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    contract = load_json(monorepo, DASHBOARD_CONTRACT_RELATIVE)

    _add(checks, defects, "contract:present", bool(contract), "present", "contract")
    _add(
        checks,
        defects,
        "contract:id",
        contract.get("contract_id") == "codestrata-insights-dashboard-contract",
        str(contract.get("contract_id")),
        "contract",
    )
    _add(
        checks,
        defects,
        "contract:presentation_only",
        contract.get("presentation_only") is True,
        str(contract.get("presentation_only")),
        "contract",
    )
    _add(
        checks,
        defects,
        "contract:validation_growth_chart_false",
        contract.get("validation_growth_chart") is False,
        str(contract.get("validation_growth_chart")),
        "contract",
    )
    _add(
        checks,
        defects,
        "contract:chart_implementation",
        contract.get("chart_implementation") == "local_css_svg_horizontal_bars",
        str(contract.get("chart_implementation")),
        "contract",
    )
    _add(
        checks,
        defects,
        "contract:overview_endpoint",
        contract.get("overview_endpoint") == "/api/v1/insights/api/overview",
        str(contract.get("overview_endpoint")),
        "contract",
    )
    _add(
        checks,
        defects,
        "contract:start_slice_16_3_false",
        contract.get("start_slice_16_3", False) is False,
        str(contract.get("start_slice_16_3", False)),
        "contract",
    )
    _add(
        checks,
        defects,
        "contract:production_deployment_disabled",
        contract.get("production_deployment_enabled") is False,
        str(contract.get("production_deployment_enabled")),
        "contract",
    )
    return checks, defects


def check_dashboard_inventory(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    _add(checks, defects, "dashboard:root", exists(monorepo, APP_ROOT), APP_ROOT, "dashboard")

    for rel in (
        "insights/src/pages/DashboardPage.tsx",
        "insights/src/components/charts/DistributionChart.tsx",
        "insights/src/components/MetricCard.tsx",
        "insights/src/components/DashboardErrorBoundary.tsx",
        "insights/src/dashboard/format.ts",
        "insights/src/dashboard/labels.ts",
        "insights/public/design-tokens/tokens.css",
    ):
        _add(
            checks,
            defects,
            f"dashboard:file:{Path(rel).name}",
            exists(monorepo, rel),
            rel,
            "dashboard",
        )

    dashboard = read_text(monorepo, "insights/src/pages/DashboardPage.tsx")
    _add(
        checks,
        defects,
        "dashboard:refresh_button",
        "Refresh dashboard" in dashboard,
        "present",
        "dashboard",
    )
    for section_id in (
        "activity",
        "assessments",
        "adoption",
        "coverage",
        "technology",
        "ai",
        "validation",
    ):
        _add(
            checks,
            defects,
            f"dashboard:section:{section_id}",
            f'id="{section_id}"' in dashboard or f"id=\"{section_id}\"" in dashboard,
            "present",
            "dashboard",
        )

    distribution = read_text(monorepo, "insights/src/components/charts/DistributionChart.tsx")
    _add(
        checks,
        defects,
        "dashboard:horizontal_bar_chart",
        "HorizontalBarChart" in distribution,
        "present",
        "dashboard",
    )
    _add(
        checks,
        defects,
        "dashboard:metric_table",
        "MetricTable" in distribution,
        "present",
        "dashboard",
    )

    metric_card = read_text(monorepo, "insights/src/components/MetricCard.tsx")
    _add(
        checks,
        defects,
        "dashboard:headline_metric_card",
        "HeadlineMetricCard" in metric_card,
        "present",
        "dashboard",
    )
    _add(
        checks,
        defects,
        "dashboard:distribution_metric",
        "DistributionMetric" in metric_card,
        "present",
        "dashboard",
    )
    _add(
        checks,
        defects,
        "dashboard:error_boundary",
        exists(monorepo, "insights/src/components/DashboardErrorBoundary.tsx")
        and "DashboardErrorBoundary" in read_text(monorepo, "insights/src/app/App.tsx"),
        "wired",
        "dashboard",
    )

    labels = read_text(monorepo, "insights/src/dashboard/labels.ts")
    _add(
        checks,
        defects,
        "dashboard:labels_ai_model_family",
        'ai_model_adoption: "AI model family adoption"' in labels,
        "exact",
        "dashboard",
    )
    _add(
        checks,
        defects,
        "dashboard:labels_validation_size",
        'validation_dataset_growth: "Validation dataset size"' in labels,
        "exact",
        "dashboard",
    )
    _add(
        checks,
        defects,
        "dashboard:labels_anonymous_installations",
        'total_anonymous_installations: "Anonymous installations"' in labels,
        "exact",
        "dashboard",
    )

    return checks, defects


def check_chart_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg = load_json(monorepo, PACKAGE_JSON)
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
    found = [name for name in FORBIDDEN_CHART_PACKAGES if name in deps]
    _add(
        checks,
        defects,
        "chart:no_forbidden_packages",
        not found,
        "absent" if not found else ",".join(found),
        "chart_boundary",
    )

    html = read_text(monorepo, "insights/index.html")
    _add(
        checks,
        defects,
        "chart:no_cdn_script_tags",
        "chart.js" not in html.lower()
        and "cdn.jsdelivr.net" not in html.lower()
        and "unpkg.com" not in html.lower(),
        "absent",
        "chart_boundary",
    )
    _add(
        checks,
        defects,
        "chart:local_css_svg_only",
        "HorizontalBarChart" in read_text(
            monorepo, "insights/src/components/charts/DistributionChart.tsx"
        )
        and "chart.js" not in dashboard_source_blob(monorepo).lower(),
        "local_css_svg",
        "chart_boundary",
    )
    return checks, defects


def check_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ui_source = "\n".join(read_text(monorepo, rel) for rel in PRIVACY_UI_FILES)
    synthetic = read_text(monorepo, "insights/src/api/syntheticMocks.ts")

    for field in PRIVACY_FORBIDDEN_FIELDS:
        _add(
            checks,
            defects,
            f"privacy:ui_no_{field}",
            field not in ui_source,
            "absent",
            "privacy",
        )
        _add(
            checks,
            defects,
            f"privacy:synthetic_no_{field}",
            field not in synthetic,
            "absent",
            "privacy",
        )

    _add(
        checks,
        defects,
        "privacy:no_users_label",
        '"Users"' not in read_text(monorepo, "insights/src/dashboard/labels.ts")
        and ">Users<" not in read_text(monorepo, "insights/src/pages/DashboardPage.tsx"),
        "absent",
        "privacy",
    )
    return checks, defects


def check_auth_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    auth_client = read_text(monorepo, "insights/src/api/authClient.ts")

    _add(
        checks,
        defects,
        "auth:client_present",
        exists(monorepo, "insights/src/api/authClient.ts"),
        "present",
        "auth_boundary",
    )
    _add(
        checks,
        defects,
        "auth:credentials_include",
        'credentials: "include"' in auth_client
        or "credentials: 'include'" in auth_client,
        "include",
        "auth_boundary",
    )
    _add(
        checks,
        defects,
        "auth:overview_requires_cookie",
        "/insights/api/overview" in auth_client,
        "present",
        "auth_boundary",
    )
    _add(
        checks,
        defects,
        "auth:protected_app",
        "ProtectedApp" in read_text(monorepo, "insights/src/app/App.tsx"),
        "present",
        "auth_boundary",
    )
    return checks, defects


def check_design_system(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    tokens = read_text(monorepo, "insights/public/design-tokens/tokens.css")
    authoritative = read_text(monorepo, "design-system/tokens/tokens.css")
    _add(
        checks,
        defects,
        "design:tokens_match",
        bool(tokens) and tokens == authoritative,
        "export_copy",
        "design_system",
    )
    mappings = load_json(monorepo, "design-system/contracts/consumer-mappings.json")
    _add(
        checks,
        defects,
        "design:consumer_registered",
        "community_insights" in (mappings.get("consumers") or {}),
        "registered",
        "design_system",
    )
    return checks, defects


def check_deployment_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)

    _add(
        checks,
        defects,
        "deployment:production_disabled",
        policy.get("production_deployment_enabled") is False,
        "disabled",
        "deployment_boundary",
    )
    _add(
        checks,
        defects,
        "deployment:ingestion_disabled",
        policy.get("production_ingestion_enabled") is False,
        "disabled",
        "deployment_boundary",
    )

    present = [rel for rel in FORBIDDEN_15_12_PATHS if exists(monorepo, rel)]
    _add(
        checks,
        defects,
        "boundary:slice_15_12_not_started",
        not present,
        "absent" if not present else ",".join(present),
        "slice_15_12_boundary",
        "slice_15_12_started",
    )

    reports = monorepo / "reports" / "verification"
    later: list[str] = []
    if reports.is_dir():
        later = sorted(
            p.name
            for p in reports.iterdir()
            if p.is_dir()
            and p.name.startswith("sv15-")
            and p.name
            not in {
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
                "sv16-1",
            }
        )
    _add(
        checks,
        defects,
        "boundary:no_later_slice_reports",
        not later,
        "absent" if not later else ",".join(later),
        "slice_15_12_boundary",
        "later_slice_started",
    )
    return checks, defects


def run_all_checks(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for fn in (
        check_policy,
        check_contract,
        check_dashboard_inventory,
        check_chart_boundary,
        check_privacy,
        check_auth_boundary,
        check_design_system,
        check_deployment_boundary,
        check_scenarios,
    ):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)

    return checks, defects
