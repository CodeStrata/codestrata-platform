"""Tests for Slice 15.11 validation verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_insights_validation.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.community_insights_validation.determinism import reports_byte_identical
from verification.community_insights_validation.fixtures import (
    POISON_INSTALLATION,
    POISON_PROMPT,
    build_fixtures,
)
from verification.community_insights_validation.inventory import load_json
from verification.community_insights_validation.reporting import write_report
from verification.community_insights_validation.runner import build_report
from verification.community_insights_validation.scenarios import VALIDATION_SCENARIOS


def test_policy() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["policy_id"] == POLICY_ID
    assert policy.get("slice") == "15.11"
    assert policy.get("start_slice_16_2", False) is False
    assert policy["offline_only"] is True
    assert policy["aws_calls_forbidden"] is True
    assert policy["production_ingestion_enabled"] is False
    assert policy["live_dashboard_data_available"] is False
    assert policy["cohort_minimum"] == 3
    assert policy["overview_single_request_required"] is True
    assert policy["polling_forbidden"] is True
    assert policy["no_new_dashboard_capability_in_15_11"] is True
    assert policy["no_metric_redefinition_in_15_11"] is True


def test_scenarios() -> None:
    assert len(VALIDATION_SCENARIOS) == 26
    assert VALIDATION_SCENARIOS[0][0] == "A"
    assert VALIDATION_SCENARIOS[-1][0] == "Z"


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("start_slice_16_2", False) is False
    assert report.release_posture["production_ingestion_enabled"] is False
    assert report.release_posture["live_dashboard_data_available"] is False
    assert report.release_posture["aws_called"] is False
    assert report.release_posture["deployed"] is False
    path = write_report(monorepo, report)
    text = Path(path).read_text(encoding="utf-8")
    assert "timestamp" not in text.lower()
    assert "/Users/" not in text
    assert POISON_INSTALLATION not in text
    assert POISON_PROMPT not in text


def test_determinism() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert reports_byte_identical(a, b)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

    path_a = write_report(monorepo, build_report(monorepo))
    path_b = write_report(monorepo, build_report(monorepo))
    assert path_a.read_bytes() == path_b.read_bytes()


def test_fixtures_poison_not_in_redacted_label() -> None:
    fx = build_fixtures()
    assert fx.expected_installations == 2
    assert fx.expected_events == 3
    assert "[redacted_install]" not in fx.poison_strings
