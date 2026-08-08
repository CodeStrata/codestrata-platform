"""Unit tests for Slice 15.12 Epic 15 completion verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_insights_completion.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    TOTAL_SLICES,
    monorepo_root_from_here,
)
from verification.community_insights_completion.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
    reports_byte_identical,
)
from verification.community_insights_completion.inventory import load_json
from verification.community_insights_completion.reporting import write_report
from verification.community_insights_completion.runner import build_report
from verification.community_insights_completion.slice_matrix import SLICE_TITLES


def test_completion_policy() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["epic"] == 15
    assert policy["slice_count"] == 12
    assert policy.get("start_slice_16_2", False) is True
    assert policy.get("start_slice_16_5", False) is True
    assert policy.get("start_slice_16_6", False) is True
    assert policy.get("start_slice_16_7", False) is True
    assert policy.get("start_slice_16_8", False) is True
    assert policy.get("start_slice_16_9", False) is True
    assert policy.get("start_slice_16_10", False) is True
    assert policy.get("start_epic_17", False) is False
    assert policy["production_ingestion_enabled"] is False
    assert policy["live_dashboard_data_available"] is False
    assert policy["insights_site_deployed"] is False
    assert policy["deployed"] is False


def test_slice_matrix_titles() -> None:
    assert len(SLICE_TITLES) == TOTAL_SLICES
    assert SLICE_TITLES["15.12"] == "Epic 15 Completion Verification"


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.completed_slices == TOTAL_SLICES
    assert report.total_slices == TOTAL_SLICES
    assert report.epic_complete is True
    assert report.release_posture.get("start_slice_16_5", False) is True
    assert report.release_posture.get("start_slice_16_6", False) is True
    assert report.release_posture.get("start_epic_17", False) is False
    assert report.release_posture.get("commit_created") is False
    assert report.release_posture.get("tag_created") is False
    assert report.release_posture.get("published") is False
    assert report.release_posture.get("deployed") is False
    assert report.release_posture.get("production_ingestion_enabled") is False
    assert report.release_posture.get("live_dashboard_data_available") is False
    assert report.release_posture.get("insights_site_deployed") is False
    assert report.release_posture.get("real_secrets_created") is False
    assert report.release_posture.get("remote_insights_repository_created") is False
    assert report.release_posture.get("epic_15_complete") is True
    assert len(report.slice_matrix) == TOTAL_SLICES
    assert all(row["completion_state"] == "complete" for row in report.slice_matrix)


def test_runner_deterministic_double_write(tmp_path: Path) -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert reports_byte_identical(a, b)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

    text = dict_to_canonical_json(a)
    safe, reason = report_text_is_safe(text)
    assert safe, reason
    assert "timestamp" not in text.lower()
    assert "/Users/" not in text
    assert "file://" not in text

    out_a = tmp_path / "a.json"
    out_b = tmp_path / "b.json"
    out_a.write_text(text, encoding="utf-8")
    out_b.write_text(dict_to_canonical_json(b), encoding="utf-8")
    assert out_a.read_bytes() == out_b.read_bytes()


def test_authoritative_report_double_write() -> None:
    monorepo = monorepo_root_from_here()
    path_a = write_report(monorepo, build_report(monorepo))
    path_b = write_report(monorepo, build_report(monorepo))
    assert path_a.read_bytes() == path_b.read_bytes()
