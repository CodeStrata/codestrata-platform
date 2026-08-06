"""Integration and determinism for Slice 9.15 completion."""

from __future__ import annotations

from verification.privacy_first_telemetry_completion.contract import (
    FORBIDDEN_REPORT_FRAGMENTS,
    monorepo_root_from_here,
)
from verification.privacy_first_telemetry_completion.models import report_contains_forbidden_leak
from verification.privacy_first_telemetry_completion.runner import (
    run_privacy_first_telemetry_completion,
)


def test_integration_pass(tmp_path) -> None:  # type: ignore[no-untyped-def]
    out = tmp_path / "sv9-15"
    report = run_privacy_first_telemetry_completion(
        monorepo=monorepo_root_from_here(),
        output_dir=out,
        write_report=True,
        run_cross_client_live=True,
    )
    assert report.verdict == "pass"
    assert report.failed_checks == 0
    assert not report.defects
    assert not report.blockers
    assert report.completed_slice_count == 15
    assert report.confirmations["epic_10_not_started"] is True
    assert report.confirmations["slices_15_of_15"] is True
    assert report.production_posture["production_collection"] == "not_operational"

    blob1 = (
        out / "privacy-first-telemetry-completion-verification.json"
    ).read_text(encoding="utf-8")
    report2 = run_privacy_first_telemetry_completion(
        monorepo=monorepo_root_from_here(),
        output_dir=tmp_path / "sv9-15-b",
        write_report=True,
        run_cross_client_live=False,
    )
    # Live cross-client may rewrite 9.14 report; compare completion JSON without
    # depending on cross-client re-run side effects by comparing stable dicts
    # from identical skip-cross-client runs.
    report3 = run_privacy_first_telemetry_completion(
        monorepo=monorepo_root_from_here(),
        output_dir=tmp_path / "sv9-15-c",
        write_report=True,
        run_cross_client_live=False,
    )
    assert report2.to_stable_json() == report3.to_stable_json()
    assert not report_contains_forbidden_leak(blob1, FORBIDDEN_REPORT_FRAGMENTS)


def test_report_excludes_paths_and_identities() -> None:
    report = run_privacy_first_telemetry_completion(
        write_report=False,
        run_cross_client_live=False,
    )
    blob = report.to_stable_json()
    assert not report_contains_forbidden_leak(blob, FORBIDDEN_REPORT_FRAGMENTS)
    assert "/Users/" not in blob
    assert "/home/" not in blob
    assert '"installation_id"' not in blob
    assert '"machineId"' not in blob
