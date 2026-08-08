"""Tests for Slice 15.2 analytics partition verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_analytics_partition.contract import (
    DASHBOARD_METRICS,
    POLICY_ID,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.community_analytics_partition.determinism import (
    reports_byte_identical,
)
from verification.community_analytics_partition.inventory import load_json
from verification.community_analytics_partition.reporting import write_report
from verification.community_analytics_partition.runner import build_report
from verification.community_analytics_partition.scenarios import PARTITION_SCENARIOS


def test_policy() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["partition_redesign_required"] is False
    assert policy.get("start_slice_16_2", False) is False
    assert set(policy["dashboard_metric_support"]) == set(DASHBOARD_METRICS)


def test_scenarios() -> None:
    assert len(PARTITION_SCENARIOS) == 15
    assert PARTITION_SCENARIOS[0][0] == "A"


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.partition_redesign_required is False
    assert report.release_posture.get("start_slice_16_2", False) is False
    assert len(report.metric_matrix) == 15
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
