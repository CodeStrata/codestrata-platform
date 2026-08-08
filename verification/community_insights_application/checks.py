"""Checks for Slice 15.8 Insights application verification."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from verification.community_insights_application.contract import (
    APP_ROOT,
    FORBIDDEN_15_9_PATHS,
    PACKAGE_JSON,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    REPO_CONTRACT_RELATIVE,
)
from verification.community_insights_application.inventory import exists, load_json, read_text
from verification.community_insights_application.models import CheckResult, Defect


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "application_defect",
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
        "policy:start_slice_16_3_false",
        policy.get("start_slice_16_3", False) is False,
        str(policy.get("start_slice_16_3", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:future_repo",
        policy.get("future_repository") == "codestrata-insights"
        and policy.get("future_visibility") == "private"
        and policy.get("future_host") == "insights.codestrata.ai",
        "private_insights",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:stack_react_vite",
        (policy.get("technology_stack") or {}).get("framework") == "react"
        and (policy.get("technology_stack") or {}).get("bundler") == "vite"
        and (policy.get("technology_stack") or {}).get("ssr") is False,
        "spa",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:auth_charts_enabled_deploy_disabled",
        policy.get("authentication_deferred_to_15_9") is False
        and policy.get("production_deploy_disabled") is True
        and policy.get("metric_charts_deferred_to_15_10") is False
        and policy.get("start_slice_16_3", False) is False,
        "charts_in_15_10",
        "policy",
    )
    contract = load_json(monorepo, REPO_CONTRACT_RELATIVE)
    _add(
        checks,
        defects,
        "policy:repo_contract",
        contract.get("contract_id") == "codestrata-insights-repository-contract",
        "present",
        "policy",
    )
    return checks, defects


def check_application(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "app:root",
        exists(monorepo, APP_ROOT),
        APP_ROOT,
        "application",
    )
    pkg = load_json(monorepo, PACKAGE_JSON)
    _add(
        checks,
        defects,
        "app:package_name",
        pkg.get("name") == "codestrata-insights",
        str(pkg.get("name")),
        "application",
    )
    for rel in (
        "insights/src/app/App.tsx",
        "insights/src/components/AppShell.tsx",
        "insights/src/pages/DashboardPage.tsx",
        "insights/src/metrics/metricResult.ts",
        "insights/src/api/insightsApi.ts",
        "insights/public/design-tokens/tokens.css",
        "insights/public/brand/codestrata-lockup-horizontal-on-light.svg",
        "insights/index.html",
    ):
        _add(checks, defects, f"app:file:{Path(rel).name}", exists(monorepo, rel), rel, "application")

    html = read_text(monorepo, "insights/index.html")
    _add(
        checks,
        defects,
        "app:robots_noindex",
        'name="robots" content="noindex,nofollow"' in html and 'lang="en"' in html,
        "noindex",
        "application",
    )
    _add(
        checks,
        defects,
        "app:internal_wording",
        "Internal Community Insights" in read_text(monorepo, "insights/src/components/AppShell.tsx"),
        "internal",
        "application",
    )

    metric_ts = read_text(monorepo, "insights/src/metrics/metricResult.ts")
    for field in (
        "metric_id",
        "status",
        "window",
        "value",
        "groups",
        "completeness",
        "denominator",
        "share",
        "limitations",
    ):
        _add(
            checks,
            defects,
            f"metric:{field}",
            field in metric_ts,
            "present",
            "metric_contract",
        )
    _add(
        checks,
        defects,
        "metric:no_installation_id_field",
        "installation_id:" not in metric_ts and "installationId" not in metric_ts,
        "clean",
        "privacy",
    )

    api = read_text(monorepo, "insights/src/api/insightsApi.ts")
    _add(
        checks,
        defects,
        "api:has_unavailable_client",
        "UnavailableInsightsApiClient" in api and "unavailable" in api,
        "present",
        "application",
    )
    _add(
        checks,
        defects,
        "api:production_default_not_mock",
        "HttpInsightsApiClient" in read_text(monorepo, "insights/src/app/App.tsx")
        and "new MockInsightsApiClient" not in read_text(monorepo, "insights/src/app/App.tsx"),
        "authenticated_http_default",
        "application",
    )

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

    src_blob = "\n".join(
        read_text(monorepo, rel)
        for rel in (
            "insights/src/main.tsx",
            "insights/src/app/App.tsx",
            "insights/src/api/insightsApi.ts",
            "insights/src/pages/DashboardPage.tsx",
            "insights/package.json",
        )
    )
    _add(
        checks,
        defects,
        "privacy:no_aws_sdk",
        "@aws-sdk" not in src_blob and "aws-sdk" not in src_blob and "boto3" not in src_blob,
        "clean",
        "privacy",
    )
    _add(
        checks,
        defects,
        "privacy:no_s3",
        "ListObjectsV2" not in src_blob and "s3://" not in src_blob,
        "clean",
        "privacy",
    )
    return checks, defects


def check_export_and_boundaries(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    scripts = monorepo / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))

    from repository_export_router.targets import ExportTarget, TARGET_REGISTRY, parse_target
    from repository_export_router.router import export_repository

    _add(
        checks,
        defects,
        "export:target_registered",
        ExportTarget.INSIGHTS in TARGET_REGISTRY
        and TARGET_REGISTRY[ExportTarget.INSIGHTS].visibility
        == "private_internal_application",
        "insights",
        "export",
    )
    _add(
        checks,
        defects,
        "export:parse_insights",
        parse_target("insights") is ExportTarget.INSIGHTS,
        "ok",
        "export",
    )

    with tempfile.TemporaryDirectory(prefix="insights-export-") as tmp:
        dest = Path(tmp) / "codestrata-insights"
        result = export_repository(
            target="insights",
            destination=dest,
            dry_run=True,
            source_root=monorepo,
        )
        _add(
            checks,
            defects,
            "export:dry_run_ok",
            result.status == "ok" and result.dry_run is True,
            result.status,
            "export",
        )
        _add(
            checks,
            defects,
            "export:private_visibility",
            result.visibility == "private_internal_application",
            result.visibility,
            "export",
        )
        _add(
            checks,
            defects,
            "export:no_git_limitation",
            "no_git_init" in result.limitation_codes,
            "present",
            "export",
        )

    present = [rel for rel in FORBIDDEN_15_9_PATHS if exists(monorepo, rel)]
    _add(
        checks,
        defects,
        "boundary:slice_15_10",
        not present,
        "absent" if not present else ",".join(present),
        "slice_15_9_boundary",
        "slice_15_10_started",
    )
    _add(
        checks,
        defects,
        "boundary:auth_owned_by_15_9",
        exists(monorepo, "verification/community_insights_auth")
        or exists(
            monorepo,
            "platform/src/codestrata_platform/community_cloud_api/insights_auth",
        ),
        "present_or_deferred_ok",
        "auth_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:no_secrets_manager_in_api_client",
        "SecretsManager" not in read_text(monorepo, "insights/src/api/insightsApi.ts")
        and "SecretsManager"
        not in read_text(monorepo, "insights/src/api/authClient.ts"),
        "absent",
        "auth_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:deploy_disabled",
        load_json(monorepo, POLICY_RELATIVE).get("production_deploy_disabled") is True,
        "disabled",
        "deployment_boundary",
    )

    reports = monorepo / "reports" / "verification"
    later = []
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
        "boundary:no_later_reports",
        not later,
        "absent" if not later else ",".join(later),
        "slice_15_9_boundary",
        "slice_15_9_started",
    )
    return checks, defects
