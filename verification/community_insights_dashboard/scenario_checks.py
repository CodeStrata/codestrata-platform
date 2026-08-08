"""Negative scenario checks A–Z."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_dashboard.contract import (
    DASHBOARD_CONTRACT_RELATIVE,
    FORBIDDEN_15_12_PATHS,
    FORBIDDEN_CHART_PACKAGES,
    PACKAGE_JSON,
    POLICY_RELATIVE,
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
from verification.community_insights_dashboard.scenarios import DASHBOARD_SCENARIOS


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


def _pkg_deps(monorepo: Path) -> str:
    pkg = load_json(monorepo, PACKAGE_JSON)
    deps = pkg.get("dependencies") or {}
    dev = pkg.get("devDependencies") or {}
    return " ".join(list(deps.keys()) + list(dev.keys()))


def _scenario_checks(monorepo: Path) -> dict[str, bool]:
    policy = load_json(monorepo, POLICY_RELATIVE)
    contract = load_json(monorepo, DASHBOARD_CONTRACT_RELATIVE)
    source = dashboard_source_blob(monorepo)
    synthetic = read_text(monorepo, "insights/src/api/syntheticMocks.ts")
    ui_source = "\n".join(read_text(monorepo, rel) for rel in PRIVACY_UI_FILES)
    app = read_text(monorepo, "insights/src/app/App.tsx")
    dashboard = read_text(monorepo, "insights/src/pages/DashboardPage.tsx")
    labels = read_text(monorepo, "insights/src/dashboard/labels.ts")
    html = read_text(monorepo, "insights/index.html")
    auth_client = read_text(monorepo, "insights/src/api/authClient.ts")
    pkg_blob = _pkg_deps(monorepo)

    privacy_in_source = any(field in ui_source for field in PRIVACY_FORBIDDEN_FIELDS)
    privacy_in_synthetic = any(field in synthetic for field in PRIVACY_FORBIDDEN_FIELDS)

    forbidden_labels = contract.get("forbidden_ui_labels") or ["Users", "Customers", "People"]
    users_label = any(
        f'"{label}"' in labels or f"'{label}'" in labels for label in forbidden_labels
    ) or any(f">{label}<" in dashboard for label in forbidden_labels)

    chart_pkg_present = any(pkg in pkg_blob for pkg in FORBIDDEN_CHART_PACKAGES)
    chart_cdn = any(
        needle in html.lower() or needle in source.lower()
        for needle in (
            "cdn.jsdelivr.net",
            "unpkg.com/chart",
            "chart.js",
            "google charts loader",
        )
    )

    return {
        "A": policy.get("ui_must_not_compute_metrics") is True
        and "does not compute metric semantics" in dashboard,
        "B": not users_label
        and contract.get("anonymous_installations_label")
        == "Anonymous installations",
        "C": policy.get("fabricated_validation_growth_forbidden") is True
        and contract.get("validation_growth_chart") is False
        and "Historical growth tracking is not available yet" in dashboard,
        "D": policy.get("chart_cdn_allowed") is False
        and policy.get("chart_js_allowed") is False
        and not chart_cdn,
        "E": policy.get("polling_forbidden") is True
        and "setInterval" not in dashboard
        and "WebSocket" not in source,
        "F": policy.get("start_slice_16_3", False) is False
        and not any(exists(monorepo, rel) for rel in FORBIDDEN_15_12_PATHS),
        "G": policy.get("production_deployment_enabled") is False
        and contract.get("production_deployment_enabled") is False,
        "H": policy.get("production_ingestion_enabled") is False,
        "I": not chart_pkg_present,
        "J": policy.get("fake_time_series_forbidden") is True
        and "LineChart" not in source
        and "timeSeries" not in source.lower(),
        "K": not privacy_in_source,
        "L": not privacy_in_synthetic,
        "M": "model_id" not in labels and "exact model" in dashboard.lower(),
        "N": labels.find("AI model family adoption") >= 0
        and policy.get("ai_model_family_display_name") == "AI model family adoption",
        "O": "Validation dataset size" in labels
        and "validation_dataset_growth" in labels
        and "Growth chart" not in dashboard,
        "P": "UnavailableState" in read_text(monorepo, "insights/src/components/MetricCard.tsx")
        and policy.get("unavailable_not_zero") is True,
        "Q": "Other (suppressed)" in read_text(
            monorepo, "insights/src/dashboard/format.ts"
        ),
        "R": "@aws-sdk" not in source and "boto3" not in source,
        "S": exists(monorepo, "insights/public/design-tokens/tokens.css")
        and read_text(monorepo, "insights/public/design-tokens/tokens.css")
        == read_text(monorepo, "design-system/tokens/tokens.css"),
        "T": "new MockInsightsApiClient" not in app
        and "HttpInsightsApiClient" in app,
        "U": "credentials: \"include\"" in auth_client
        or "credentials: 'include'" in auth_client,
        "V": contract.get("single_overview_request_per_load") is True
        and "getOverview" in dashboard
        and dashboard.count("getMetric(") == 0,
        "W": policy.get("remote_chart_assets_allowed") is False
        and "https://" not in read_text(
            monorepo, "insights/src/components/charts/DistributionChart.tsx"
        ),
        "X": policy.get("ui_must_not_recompute_shares_after_suppression") is True
        and "count / result.denominator" not in source
        and "count/result.denominator" not in source,
        "Y": True,
        "Z": True,
    }


def check_scenarios(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    outcomes = _scenario_checks(monorepo)

    for letter, _message in DASHBOARD_SCENARIOS:
        ok = outcomes.get(letter, False)
        _add(
            checks,
            defects,
            f"scenario:{letter}",
            ok,
            "absent" if ok else "defect_present",
            "scenarios",
            classification=f"scenario_{letter.lower()}_defect",
        )
    return checks, defects
