"""Tests for Slice 15.1 Community Data Lake audit."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_data_lake_audit.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.community_data_lake_audit.determinism import reports_byte_identical
from verification.community_data_lake_audit.findings import AUDIT_FINDINGS
from verification.community_data_lake_audit.inventory import load_json
from verification.community_data_lake_audit.runner import build_report, write_report
from verification.community_data_lake_audit.scenarios import AUDIT_SCENARIOS


def test_policy() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy.get("start_slice_16_2", False) is False
    assert policy["telemetry_redesign_allowed"] is False
    assert policy["dashboard_ready_for_implementation"] is False
    assert policy["dashboard_storage_contract_ready"] is True


def test_findings_cover_required_classes() -> None:
    classes = {f.classification for f in AUDIT_FINDINGS}
    assert {"Accepted", "Historical", "Deferred"}.issubset(classes)
    assert len(AUDIT_FINDINGS) >= 20


def test_scenarios() -> None:
    assert len(AUDIT_SCENARIOS) == 20
    assert AUDIT_SCENARIOS[0][0] == "A"
    assert AUDIT_SCENARIOS[-1][0] == "T"


def test_build_and_write_report(tmp_path: Path) -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("start_slice_16_2", False) is False
    assert report.release_posture["dashboard_built"] is False
    assert report.slice_15_7_boundary_status == "pass"
    path = write_report(monorepo, report)
    text = Path(path).read_text(encoding="utf-8")
    assert "timestamp" not in text.lower()
    assert "/Users/" not in text
    # also exercise temp serialization
    (tmp_path / "out.json").write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_determinism() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert reports_byte_identical(a, b)
