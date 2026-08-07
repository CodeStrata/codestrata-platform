"""Tests for Slice 12.2 Cursor release-surface removal verification."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_release_surface_removal.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
)
from verification.cursor_release_surface_removal.runner import (
    build_cursor_release_surface_removal_report,
    run_cursor_release_surface_removal_verification,
)
from verification.cursor_release_surface_removal.scenarios import check_scenarios
from verification.cursor_release_surface_removal.surfaces import (
    check_build_surfaces,
    check_marketplace_surfaces,
    check_package_surfaces,
    check_release_inventory,
)

REPO = Path(__file__).resolve().parents[3]


def test_contract_schema() -> None:
    contract = default_contract()
    assert contract.schema_name == SCHEMA_NAME == "cursor-release-surface-removal-verification"
    assert contract.schema_version == SCHEMA_VERSION == "1.0.0"
    assert contract.start_slice_12_3 is False


def test_build_and_package_surfaces() -> None:
    checks, defects = check_build_surfaces(REPO)
    assert all(c.ok for c in checks), [c for c in checks if not c.ok]
    assert defects == []
    checks, defects = check_package_surfaces(REPO)
    assert all(c.ok for c in checks)
    assert defects == []


def test_marketplace_and_inventory() -> None:
    checks, defects = check_marketplace_surfaces(REPO)
    assert all(c.ok for c in checks), [c for c in checks if not c.ok]
    assert defects == []
    checks, defects = check_release_inventory(REPO)
    assert all(c.ok for c in checks), [c for c in checks if not c.ok]
    assert defects == []


def test_negative_scenarios() -> None:
    checks, defects = check_scenarios(REPO)
    assert len(checks) >= 26
    assert all(c.ok for c in checks), [c.name for c in checks if not c.ok]
    assert defects == []


def test_build_report_static() -> None:
    report = build_cursor_release_surface_removal_report(
        monorepo=REPO,
        run_vscode_compile=False,
        run_vscode_tests=False,
        run_vscode_package=False,
    )
    assert report.schema_name == SCHEMA_NAME
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.cursor_release_inventory_status == "pass"


def test_determinism(tmp_path: Path) -> None:
    a = build_cursor_release_surface_removal_report(
        monorepo=REPO,
        run_vscode_compile=False,
        run_vscode_tests=False,
        run_vscode_package=False,
    )
    b = build_cursor_release_surface_removal_report(
        monorepo=REPO,
        run_vscode_compile=False,
        run_vscode_tests=False,
        run_vscode_package=False,
    )
    assert a.to_dict() == b.to_dict()
    from verification.cursor_release_surface_removal.reporting import write_verification_outputs

    pa, _ = write_verification_outputs(a, tmp_path / "a")
    pb, _ = write_verification_outputs(b, tmp_path / "b")
    assert pa.read_bytes() == pb.read_bytes()


def test_runner_writes_report(tmp_path: Path) -> None:
    report = run_cursor_release_surface_removal_verification(
        monorepo=REPO,
        output_dir=tmp_path,
        write_report=True,
        run_vscode_compile=False,
        run_vscode_tests=False,
        run_vscode_package=False,
        check_determinism_pair=True,
    )
    path = tmp_path / "cursor-release-surface-removal-verification.json"
    assert path.is_file()
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert "/Users/" not in path.read_text()
