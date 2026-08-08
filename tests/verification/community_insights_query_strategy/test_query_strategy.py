"""Tests for Slice 15.5 query strategy verification."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from codestrata_platform.community_cloud_api.insights_query.errors import (
    InsightsQueryPlanError,
)
from codestrata_platform.community_cloud_api.insights_query.models import DateWindow
from codestrata_platform.community_cloud_api.insights_query.planner import (
    plan_metric_query,
    reject_caller_prefix,
)
from verification.community_insights_query_strategy.contract import (
    LAKE_METRICS,
    POLICY_ID,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.community_insights_query_strategy.determinism import (
    reports_byte_identical,
)
from verification.community_insights_query_strategy.inventory import load_json
from verification.community_insights_query_strategy.reporting import write_report
from verification.community_insights_query_strategy.runner import build_report
from verification.community_insights_query_strategy.scenarios import QUERY_SCENARIOS


def test_policy() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["policy_id"] == POLICY_ID
    assert policy["athena_required"] is False
    assert policy.get("start_slice_16_2", False) is False
    assert policy["quarantine_query_forbidden"] is True


def test_scenarios() -> None:
    assert len(QUERY_SCENARIOS) == 26
    assert QUERY_SCENARIOS[0][0] == "A"
    assert QUERY_SCENARIOS[-1][0] == "Z"


def test_planner_rejects_raw_root_and_caller_prefix() -> None:
    try:
        reject_caller_prefix("raw/")
        assert False
    except InsightsQueryPlanError as exc:
        assert exc.code == "invalid_query_window"


def test_planner_dau_and_lifetime() -> None:
    day = date(2026, 8, 8)
    dau = plan_metric_query(
        metric="daily_active_installations", window=DateWindow(day, day)
    )
    assert all("/day=08/" in p for p in dau.prefixes)
    assert not any(p.startswith("quarantine/") for p in dau.prefixes)
    life = plan_metric_query(
        metric="total_anonymous_installations",
        window=DateWindow(day - timedelta(days=10), day),
    )
    assert life.budgets.max_objects_per_query == 2000


def test_matrix_covers_lake_metrics() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    matrix = policy["metric_query_matrix"]
    for metric in LAKE_METRICS:
        assert metric in matrix
        assert matrix[metric]["direct_s3_suitable"] is True
    assert matrix["validation_dataset_growth"]["s3_query"] is False


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.athena_required is False
    assert report.release_posture.get("start_slice_16_2", False) is False
    path = write_report(monorepo, report)
    text = Path(path).read_text(encoding="utf-8")
    assert "timestamp" not in text.lower()
    assert "/Users/" not in text


def test_determinism() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert reports_byte_identical(a, b)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
