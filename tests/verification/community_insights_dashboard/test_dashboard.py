"""Tests for Slice 15.10 dashboard verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_insights_dashboard.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.community_insights_dashboard.determinism import reports_byte_identical
from verification.community_insights_dashboard.inventory import load_json
from verification.community_insights_dashboard.reporting import write_report
from verification.community_insights_dashboard.runner import build_report
from verification.community_insights_dashboard.scenarios import DASHBOARD_SCENARIOS


def test_policy() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["policy_id"] == POLICY_ID
    assert policy.get("start_slice_16_2", False) is False
    assert policy["ui_must_not_compute_metrics"] is True
    assert policy["chart_library"] == "local_css_svg"
    assert policy["chart_js_allowed"] is False
    assert policy["chart_cdn_allowed"] is False
    assert policy["fake_time_series_forbidden"] is True
    assert policy["fabricated_validation_growth_forbidden"] is True
    assert policy["overview_batch_preferred"] is True
    assert policy["polling_forbidden"] is True
    assert policy["production_deployment_enabled"] is False
    assert policy["production_ingestion_enabled"] is False
    assert policy["ai_model_family_display_name"] == "AI model family adoption"
    assert policy["display_names"]["total_anonymous_installations"] == "Anonymous installations"
    assert policy["display_names"]["validation_dataset_growth"] == "Validation dataset size"


def test_scenarios() -> None:
    assert len(DASHBOARD_SCENARIOS) == 26
    assert DASHBOARD_SCENARIOS[0][0] == "A"
    assert DASHBOARD_SCENARIOS[-1][0] == "Z"


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("start_slice_16_2", False) is False
    assert report.release_posture["metric_charts_built"] is True
    assert report.release_posture["deployed"] is False
    assert report.release_posture["ingestion_enabled"] is False
    assert report.release_posture["chart_cdn"] is False
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

    path_a = write_report(monorepo, build_report(monorepo))
    path_b = write_report(monorepo, build_report(monorepo))
    assert path_a.read_bytes() == path_b.read_bytes()
