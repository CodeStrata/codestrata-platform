"""Slice 10.8 verification package tests."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_privacy.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.anonymous_analytics_privacy.models import report_contains_forbidden_leak
from verification.anonymous_analytics_privacy.runner import (
    run_anonymous_analytics_privacy_verification,
)


def test_contract_tokens() -> None:
    contract = default_contract()
    assert contract.schema_name == SCHEMA_NAME
    assert contract.schema_version == SCHEMA_VERSION
    assert contract.start_slice_109 is False
    assert contract.no_shared_runtime_schema is True


def test_verification_pass() -> None:
    report = run_anonymous_analytics_privacy_verification(write_report=False)
    assert report.verdict == "pass"
    assert report.failed_checks == 0
    assert report.defects == []
    assert report.total_checks >= 100


def test_report_determinism_and_no_leaks(tmp_path: Path) -> None:
    out = tmp_path / "sv10-8"
    a = run_anonymous_analytics_privacy_verification(output_dir=out, write_report=True)
    b = run_anonymous_analytics_privacy_verification(write_report=False)
    assert a.to_stable_json() == b.to_stable_json()
    blob = (out / "anonymous-analytics-privacy-verification.json").read_text(
        encoding="utf-8"
    )
    assert report_contains_forbidden_leak(blob) == []
    assert '"installation_id":' not in blob
    assert "/Users/" not in blob


def test_monorepo_root_resolves() -> None:
    root = monorepo_root_from_here()
    assert (root / "engine").is_dir()
    assert (root / "vscode-plugin").is_dir()
    assert (root / "verification" / "anonymous_analytics_privacy").is_dir()
