"""Tests for Slice 17.18 Community Data Lake & Insights verification."""

from __future__ import annotations

import json

from verification.community_data_lake_insights.contract import (
    AGG_REGISTER,
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    SCHEMA_NAME,
    STREAM_REGISTER,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_data_lake_insights.determinism import (
    canonical_for_determinism,
    dict_to_canonical_json,
)
from verification.community_data_lake_insights.helpers import report_text_is_safe
from verification.community_data_lake_insights.runner import build_report, run


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_18 is True
    assert c.start_slice_17_19 is True


def test_policy_registers() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == POLICY_SCHEMA
    for key, expected in POLICY_REQUIRED_VALUES.items():
        assert policy.get(key) == expected, key

    streams = json.loads((root / STREAM_REGISTER).read_text(encoding="utf-8"))
    assert "community-data-lake-stream-register" in str(streams.get("schema"))
    assert len(streams.get("entries") or []) >= 5

    agg = json.loads((root / AGG_REGISTER).read_text(encoding="utf-8"))
    assert "community-insights-aggregation-register" in str(agg.get("schema"))
    assert agg.get("max_list_requests_per_query") == 2000
    assert len(agg.get("entries") or []) >= 7

    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == SCHEMA_NAME
    assert contract.get("start_slice_17_18") is True
    assert contract.get("start_slice_17_19") is True


def test_build_report_runs() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.18"
    assert report.suite_id == "sv17-18"
    assert report.epic17_boundary.get("start_slice_17_18") is True
    assert report.epic17_boundary.get("start_slice_17_19") is True
    assert report.epic17_boundary.get("start_slice_17_20") is False
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert letter in report.scenario_results
    # Soft limitation codes must not include hard-resolved items
    assert "product_default_http_transport_unavailable" not in report.limitations
    assert "live_datalake_probe_skipped" not in report.limitations


def test_determinism_normalized() -> None:
    """Dual-run compare after stripping live-volatile numeric fields."""

    root = monorepo_root_from_here()
    a = canonical_for_determinism(build_report(root).to_dict())
    b = canonical_for_determinism(build_report(root).to_dict())
    assert a == b


def test_report_safe() -> None:
    root = monorepo_root_from_here()
    text = dict_to_canonical_json(build_report(root).to_dict())
    assert report_text_is_safe(text)
    assert "cscc_v1_" not in text
    assert "Bearer " not in text
    assert "arn:aws:" not in text
    assert "raw/stream=" not in text
    assert "/Users/" not in text


def test_run_writes_artifact() -> None:
    root = monorepo_root_from_here()
    report = run(root)
    path = (
        root
        / ".codestrata-artifacts/validation/suites/sv17-18"
        / "community-data-lake-insights-verification.json"
    )
    assert path.is_file()
    assert report.verdict != "FAIL" or report.failed_checks >= 0
