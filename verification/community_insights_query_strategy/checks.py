"""Checks for Slice 15.5 query strategy verification."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from verification.community_insights_query_strategy.aggregation_boundary import (
    aggregation_absent,
)
from verification.community_insights_query_strategy.contract import (
    CONTRACT_RELATIVE,
    DOC_RELATIVE,
    FORBIDDEN_15_7_PATHS,
    LAKE_METRICS,
    PLANNER_MODULE,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
)
from verification.community_insights_query_strategy.dashboard_boundary import (
    dashboard_absent,
)
from verification.community_insights_query_strategy.inventory import (
    exists,
    load_json,
    read_text,
)
from verification.community_insights_query_strategy.metric_query_matrix import (
    matrix_rows,
)
from verification.community_insights_query_strategy.models import CheckResult, Defect
from verification.community_insights_query_strategy.performance_fixtures import (
    FIXTURES,
    fixture_within_budgets,
)
from verification.community_insights_query_strategy.policy import load_query_policy


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "query_strategy_defect",
) -> None:
    checks.append(CheckResult(name, ok, detail, category))
    if not ok:
        defects.append(Defect(classification, category, "pass", detail))


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_query_policy(monorepo)
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
        "policy:doc",
        exists(monorepo, DOC_RELATIVE),
        DOC_RELATIVE,
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:contract",
        load_json(monorepo, CONTRACT_RELATIVE).get("contract_id")
        == "community-insights-query-contract",
        "present",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:direct_s3",
        policy.get("direct_s3_read_strategy") == "preferred",
        str(policy.get("direct_s3_read_strategy")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:athena_false",
        policy.get("athena_required") is False
        and policy.get("glue_required") is False
        and policy.get("database_required") is False
        and policy.get("redis_required") is False,
        "not_required",
        "athena",
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
        "policy:quarantine_forbidden",
        policy.get("quarantine_query_forbidden") is True
        and policy.get("raw_root_list_forbidden") is True
        and policy.get("arbitrary_caller_prefix_forbidden") is True,
        "locked",
        "privacy",
    )
    _add(
        checks,
        defects,
        "policy:utc",
        policy.get("timezone") == "UTC",
        str(policy.get("timezone")),
        "policy",
    )
    return checks, defects


def check_planner(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "planner:module_present",
        exists(monorepo, PLANNER_MODULE),
        PLANNER_MODULE,
        "planner",
    )
    text = read_text(monorepo, PLANNER_MODULE)
    _add(
        checks,
        defects,
        "planner:sdk_free",
        "import boto3" not in text
        and "import botocore" not in text
        and "from boto3" not in text
        and "from botocore" not in text,
        "sdk_free",
        "planner",
    )
    try:
        from codestrata_platform.community_cloud_api.insights_query.errors import (
            InsightsQueryPlanError,
        )
        from codestrata_platform.community_cloud_api.insights_query.models import (
            DateWindow,
        )
        from codestrata_platform.community_cloud_api.insights_query.planner import (
            plan_metric_query,
            plan_prefixes,
            reject_caller_prefix,
        )

        day = date(2026, 8, 8)
        plan = plan_metric_query(
            metric="daily_active_installations",
            window=DateWindow(day, day),
        )
        _add(
            checks,
            defects,
            "planner:dau_single_day",
            all(p.startswith("raw/stream=") and "/day=08/" in p for p in plan.prefixes)
            and "quarantine/" not in "".join(plan.prefixes),
            str(len(plan.prefixes)),
            "planner",
        )
        _add(
            checks,
            defects,
            "planner:no_raw_root",
            "raw/" not in plan.prefixes and all(len(p) > 4 for p in plan.prefixes),
            "bounded",
            "planner",
        )

        # Arbitrary caller prefix rejected
        rejected = False
        try:
            reject_caller_prefix("raw/")
        except InsightsQueryPlanError:
            rejected = True
        _add(
            checks,
            defects,
            "planner:reject_caller_prefix",
            rejected,
            "rejected",
            "planner",
        )

        # Quarantine stream rejected
        q_rejected = False
        try:
            plan_prefixes(
                streams=("quarantine",),
                window=DateWindow(day, day),
            )
        except InsightsQueryPlanError:
            q_rejected = True
        _add(
            checks,
            defects,
            "planner:reject_quarantine",
            q_rejected,
            "rejected",
            "planner",
        )

        # Span exceeded
        span_rejected = False
        try:
            plan_metric_query(
                metric="successful_assessments",
                window=DateWindow(day, day + timedelta(days=40)),
            )
        except InsightsQueryPlanError as exc:
            span_rejected = exc.code == "invalid_query_window"
        _add(
            checks,
            defects,
            "planner:reject_overspan",
            span_rejected,
            "rejected",
            "planner",
        )

        # Unsupported schema
        schema_rejected = False
        try:
            plan_prefixes(
                streams=("telemetry",),
                schema_versions=("9.9",),
                window=DateWindow(day, day),
            )
        except InsightsQueryPlanError as exc:
            schema_rejected = exc.code == "unsupported_schema_version"
        _add(
            checks,
            defects,
            "planner:reject_bad_schema",
            schema_rejected,
            "rejected",
            "planner",
        )

        # External metric
        ext_rejected = False
        try:
            plan_metric_query(
                metric="validation_dataset_growth",
                window=DateWindow(day, day),
            )
        except InsightsQueryPlanError:
            ext_rejected = True
        _add(
            checks,
            defects,
            "planner:external_no_s3",
            ext_rejected,
            "external",
            "planner",
        )

        # Lifetime metric allows 365 but still budgets
        life = plan_metric_query(
            metric="total_anonymous_installations",
            window=DateWindow(day - timedelta(days=30), day),
        )
        _add(
            checks,
            defects,
            "planner:lifetime_budgets",
            life.budgets.max_objects_per_query == 2000
            and life.budgets.max_bytes_per_query == 100_000_000,
            "budgeted",
            "planner",
        )

        # Cross-stream release adoption
        rel = plan_metric_query(
            metric="release_adoption",
            window=DateWindow(day, day),
        )
        streams = {p.split("/")[1].split("=", 1)[1] for p in rel.prefixes}
        _add(
            checks,
            defects,
            "planner:cross_stream_release",
            streams == {"cli_event", "extension_event"},
            str(sorted(streams)),
            "planner",
        )
    except Exception as exc:  # noqa: BLE001
        _add(checks, defects, "planner:runtime", False, type(exc).__name__, "planner")
    return checks, defects


def check_budgets_lifetime_matrix(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_query_policy(monorepo)
    budgets = dict(policy.get("budgets") or {})
    for key in (
        "max_keys_per_page",
        "max_pages_per_query",
        "max_list_requests_per_query",
        "max_get_requests_per_query",
        "max_objects_per_query",
        "max_bytes_per_query",
        "max_single_object_bytes",
    ):
        _add(
            checks,
            defects,
            f"budgets:{key}",
            isinstance(budgets.get(key), int) and int(budgets[key]) > 0,
            str(budgets.get(key)),
            "budget",
        )
    _add(
        checks,
        defects,
        "budgets:single_object_70k",
        budgets.get("max_single_object_bytes") == 70000,
        str(budgets.get("max_single_object_bytes")),
        "budget",
    )
    life = policy.get("lifetime_metric_strategy") or {}
    _add(
        checks,
        defects,
        "lifetime:strategy",
        life.get("decision")
        == "retention_window_with_hard_budgets_and_future_checkpoint",
        str(life.get("decision")),
        "budget",
    )
    _add(
        checks,
        defects,
        "lifetime:future_checkpoint",
        life.get("future_aggregation_state_required") is True,
        "15.7",
        "budget",
    )
    first = policy.get("first_repeat_assessment_strategy") or {}
    _add(
        checks,
        defects,
        "first_repeat:checkpoint",
        first.get("future_aggregation_state_required") is True,
        "15.7",
        "budget",
    )
    rows = matrix_rows(monorepo)
    _add(
        checks,
        defects,
        "matrix:count",
        len(rows) == 15,
        str(len(rows)),
        "budget",
    )
    by_id = {r["metric"]: r for r in rows}
    for metric in LAKE_METRICS:
        _add(
            checks,
            defects,
            f"matrix:{metric}:present",
            metric in by_id and bool(by_id[metric].get("streams")),
            "present",
            "budget",
        )
    _add(
        checks,
        defects,
        "matrix:validation_external",
        by_id.get("validation_dataset_growth", {}).get("s3_query") is False
        and by_id.get("validation_dataset_growth", {}).get("query_strategy")
        == "external_metric_source",
        "external",
        "budget",
    )
    # Performance fixtures
    max_objects = int(budgets.get("max_objects_per_query") or 0)
    max_bytes = int(budgets.get("max_bytes_per_query") or 0)
    for name, expected_ok in (
        ("tiny", True),
        ("product_discovery", True),
        ("near_limit", True),
        ("over_object_limit", False),
        ("over_byte_limit", False),
        ("lifetime_365", False),
    ):
        ok = fixture_within_budgets(name, max_objects=max_objects, max_bytes=max_bytes)
        _add(
            checks,
            defects,
            f"fixtures:{name}",
            ok is expected_ok and name in FIXTURES,
            f"within={ok}",
            "budget",
        )
    return checks, defects, rows, budgets


def check_privacy_iam_partial(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_query_policy(monorepo)
    forbidden = set(policy.get("forbidden_prefix_dimensions") or [])
    for dim in (
        "installation_id",
        "provider_family",
        "model_family",
        "primary_language",
    ):
        _add(
            checks,
            defects,
            f"privacy:forbid_{dim}",
            dim in forbidden,
            "forbidden",
            "privacy",
        )
    iam = policy.get("iam_reader_minimum") or {}
    _add(
        checks,
        defects,
        "iam:allow_list_get",
        set(iam.get("allow") or {}) == {"s3:ListBucket", "s3:GetObject"},
        str(iam.get("allow")),
        "privacy",
    )
    _add(
        checks,
        defects,
        "iam:deny_put",
        "s3:PutObject" in (iam.get("deny") or []),
        "deny_put",
        "privacy",
    )
    _add(
        checks,
        defects,
        "iam:unattached",
        iam.get("attached_in_15_5") is False,
        "unattached",
        "privacy",
    )
    partial = policy.get("partial_result_behavior") or {}
    _add(
        checks,
        defects,
        "partial:no_false_complete",
        partial.get("budget_exceeded_must_not_claim_complete") is True,
        "honest",
        "privacy",
    )
    errors = set(policy.get("error_taxonomy") or [])
    for code in (
        "invalid_query_window",
        "query_limit_exceeded",
        "object_limit_exceeded",
        "byte_limit_exceeded",
    ):
        _add(
            checks,
            defects,
            f"errors:{code}",
            code in errors,
            "present",
            "privacy",
        )
    _add(
        checks,
        defects,
        "cache:optional_no_redis",
        policy.get("cache_optional") is True
        and policy.get("distributed_cache_required") is False,
        "optional",
        "athena",
    )
    return checks, defects


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "boundary:aggregation",
        aggregation_absent(monorepo),
        "absent",
        "aggregation_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:dashboard",
        dashboard_absent(monorepo),
        "absent",
        "dashboard_boundary",
    )
    present = [rel for rel in FORBIDDEN_15_7_PATHS if exists(monorepo, rel)]
    _add(
        checks,
        defects,
        "boundary:slice_15_7_paths",
        not present,
        "absent" if not present else ",".join(present),
        "slice_15_7_boundary",
        "slice_15_7_started",
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
            not in {"sv15-1", "sv15-2", "sv15-3", "sv15-4", "sv15-5", "sv15-6", "sv15-7", "sv15-8", "sv15-9", "sv15-10", "sv15-11", "sv15-12", "sv16-1"}
        )
    _add(
        checks,
        defects,
        "boundary:no_later_reports",
        not later,
        "absent" if not later else ",".join(later),
        "slice_15_7_boundary",
        "slice_15_7_started",
    )
    # No Athena package
    _add(
        checks,
        defects,
        "boundary:no_athena_package",
        not exists(monorepo, "verification/community_insights_athena"),
        "absent",
        "athena",
    )
    return checks, defects
