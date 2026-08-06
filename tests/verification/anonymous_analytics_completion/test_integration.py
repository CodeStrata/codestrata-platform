"""Integration and determinism tests for Slice 10.9 completion verification."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.contract import (
    FORBIDDEN_REPORT_FRAGMENTS,
    monorepo_root_from_here,
)
from verification.anonymous_analytics_completion.models import report_contains_forbidden_leak
from verification.anonymous_analytics_completion.runner import (
    run_anonymous_analytics_completion,
)


def test_integration_pass(tmp_path: Path) -> None:
    out = tmp_path / "sv10-9"
    report = run_anonymous_analytics_completion(
        monorepo=monorepo_root_from_here(),
        output_dir=out,
        write_report=True,
        rerun_privacy_live=True,
    )
    assert report.verdict == "pass", report.defects
    assert report.failed_checks == 0
    assert not report.defects
    assert not report.blockers
    assert report.completed_slice_count == 9
    assert report.privacy_verification_status == "pass"
    assert report.confirmations["privacy_verification_rerun_pass"] is True
    assert report.confirmations["slices_9_of_9"] is True
    assert report.confirmations["epic_11_not_started"] is True
    assert report.confirmations["openrouter_absent"] is True
    assert report.production_posture == "contracts_only_not_operational"

    blob = (out / "anonymous-analytics-completion-verification.json").read_text(
        encoding="utf-8"
    )
    assert not report_contains_forbidden_leak(blob, FORBIDDEN_REPORT_FRAGMENTS)


def test_report_determinism(tmp_path: Path) -> None:
    report_a = run_anonymous_analytics_completion(
        monorepo=monorepo_root_from_here(),
        output_dir=tmp_path / "sv10-9-a",
        write_report=True,
        rerun_privacy_live=False,
    )
    report_b = run_anonymous_analytics_completion(
        monorepo=monorepo_root_from_here(),
        output_dir=tmp_path / "sv10-9-b",
        write_report=True,
        rerun_privacy_live=False,
    )
    assert report_a.to_stable_json() == report_b.to_stable_json()


def test_report_excludes_paths_and_identities() -> None:
    report = run_anonymous_analytics_completion(write_report=False)
    blob = report.to_stable_json()
    assert not report_contains_forbidden_leak(blob, FORBIDDEN_REPORT_FRAGMENTS)
    assert "/Users/" not in blob
    assert "/home/" not in blob
    assert '"installation_id"' not in blob
    assert '"machineId"' not in blob
