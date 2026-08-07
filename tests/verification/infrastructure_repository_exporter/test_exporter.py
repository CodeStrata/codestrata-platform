"""Tests for Slice 12.6 Infrastructure repository exporter."""

from __future__ import annotations

from pathlib import Path

from verification.infrastructure_repository_exporter.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.infrastructure_repository_exporter.determinism import digests_match
from verification.infrastructure_repository_exporter.runner import build_report


def test_contract_flags() -> None:
    c = default_contract()
    assert c.start_slice_12_7 is False
    assert c.no_git is True
    assert c.no_aws is True
    assert c.no_opentofu_exec is True
    assert c.schema_name == SCHEMA_NAME
    assert c.schema_version == SCHEMA_VERSION


def test_build_report_contract() -> None:
    report = build_report(monorepo_root_from_here())
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.failed_checks == 0
    assert report.fixture_export_status == "pass"
    assert report.git_boundary_status == "pass"
    assert "export_infrastructure_repository.py" in report.implementation_command


def test_runner_twice_byte_identical(tmp_path: Path) -> None:
    _ = tmp_path
    ok, ha, hb = digests_match(monorepo_root_from_here())
    assert ok, (ha, hb)
