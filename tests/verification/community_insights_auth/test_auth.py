"""Tests for Slice 15.9 auth verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_insights_auth.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.community_insights_auth.determinism import reports_byte_identical
from verification.community_insights_auth.inventory import load_json
from verification.community_insights_auth.reporting import write_report
from verification.community_insights_auth.runner import build_report
from verification.community_insights_auth.scenarios import AUTH_SCENARIOS


def test_policy() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["policy_id"] == POLICY_ID
    assert policy.get("start_slice_16_2", False) is False
    assert policy["shared_password_auth"] is True
    assert policy["production_deployment_enabled"] is False


def test_scenarios() -> None:
    assert len(AUTH_SCENARIOS) == 26
    assert AUTH_SCENARIOS[0][0] == "A"
    assert AUTH_SCENARIOS[-1][0] == "Z"


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("start_slice_16_2", False) is False
    assert report.release_posture["aws_called"] is False
    assert report.release_posture["secrets_manager_values_created"] is False
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
