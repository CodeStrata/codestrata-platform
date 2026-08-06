"""Scenarios, determinism, integration, report safety."""

from __future__ import annotations

from verification.privacy_first_telemetry.contract import monorepo_root_from_here
from verification.privacy_first_telemetry.determinism import check_determinism
from verification.privacy_first_telemetry.models import report_contains_forbidden_leak
from verification.privacy_first_telemetry.runner import (
    run_cross_client_telemetry_privacy_verification,
)
from verification.privacy_first_telemetry.scenarios import check_scenarios
from verification.privacy_first_telemetry.vscode_inputs import load_vscode_inventory


def test_scenarios() -> None:
    vscode = load_vscode_inventory(monorepo_root_from_here())
    checks, defects = check_scenarios(vscode)
    assert not defects
    assert all(c.ok for c in checks)
    assert len(checks) >= 26


def test_determinism() -> None:
    checks, defects = check_determinism()
    assert not defects
    assert all(c.ok for c in checks)


def test_integration_pass(tmp_path) -> None:  # type: ignore[no-untyped-def]
    out = tmp_path / "sv9-14"
    report = run_cross_client_telemetry_privacy_verification(
        monorepo=monorepo_root_from_here(),
        output_dir=out,
        write_report=True,
    )
    assert report.verdict == "pass"
    assert report.failed_checks == 0
    assert not report.defects
    assert report.schema_name == "cross-client-telemetry-privacy-verification"
    assert report.schema_version == "1.0.0"
    assert report.confirmations["slice_915_not_started"] is True
    assert report.confirmations["no_shared_runtime_schema"] is True
    assert report.confirmations["cursor_unchanged"] is True

    blob1 = (out / "cross-client-telemetry-privacy-verification.json").read_text(
        encoding="utf-8"
    )
    report2 = run_cross_client_telemetry_privacy_verification(
        monorepo=monorepo_root_from_here(),
        output_dir=tmp_path / "sv9-14-b",
        write_report=True,
    )
    blob2 = report2.to_stable_json()
    assert blob1 == blob2
    assert not report_contains_forbidden_leak(blob1)


def test_report_excludes_paths_and_identities() -> None:
    report = run_cross_client_telemetry_privacy_verification(write_report=False)
    blob = report.to_stable_json()
    assert "/Users/" not in blob
    assert "/home/" not in blob
    assert '"installation_id"' not in blob
    assert '"machineId"' not in blob
    assert "-----BEGIN" not in blob
