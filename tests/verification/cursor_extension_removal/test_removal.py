"""Tests for Slice 12.1 Cursor extension removal verification."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_extension_removal.classification import build_classification
from verification.cursor_extension_removal.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
)
from verification.cursor_extension_removal.inventory import (
    TRACKED_CURSOR_RELATIVE_PATHS,
    build_inventory,
)
from verification.cursor_extension_removal.removal import check_removal
from verification.cursor_extension_removal.runner import (
    build_cursor_extension_removal_report,
    run_cursor_extension_removal_verification,
)
from verification.cursor_extension_removal.scenarios import check_scenarios

REPO = Path(__file__).resolve().parents[3]


def test_contract_schema() -> None:
    contract = default_contract()
    assert contract.schema_name == SCHEMA_NAME == "cursor-extension-removal-verification"
    assert contract.schema_version == SCHEMA_VERSION == "1.0.0"
    assert contract.start_slice_12_2 is False
    assert contract.no_commit is True


def test_inventory_shows_cursor_absent() -> None:
    inv = build_inventory(REPO)
    assert inv["cursor_directory_exists"] is False
    assert inv["cursor_package_json_exists"] is False
    assert inv["cursor_src_exists"] is False
    assert inv["vscode_directory_exists"] is True
    assert inv["tracked_cursor_path_count"] == len(TRACKED_CURSOR_RELATIVE_PATHS)


def test_removal_checks_pass() -> None:
    checks, defects, removed = check_removal(REPO)
    assert removed == len(TRACKED_CURSOR_RELATIVE_PATHS)
    assert all(c.ok for c in checks)
    assert defects == []


def test_classification_buckets() -> None:
    data = build_classification()
    assert "remove_now" in data
    assert "preserve_shared" in data
    assert "defer_build_release_cleanup" in data
    assert "defer_documentation_cleanup" in data
    assert "defer_contract_retirement" in data
    assert any("vscode-plugin" in item for item in data["preserve_shared"])


def test_negative_scenarios_pass() -> None:
    checks, defects = check_scenarios(REPO)
    assert len(checks) >= 26
    assert all(c.ok for c in checks), [c.name for c in checks if not c.ok]
    assert defects == []


def test_build_report_static() -> None:
    report = build_cursor_extension_removal_report(
        monorepo=REPO,
        run_vscode_compile=False,
        run_vscode_tests=False,
    )
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.cursor_directory_status == "absent"
    assert report.cursor_package_status == "absent"
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}


def test_determinism_two_static_builds(tmp_path: Path) -> None:
    a = build_cursor_extension_removal_report(
        monorepo=REPO,
        run_vscode_compile=False,
        run_vscode_tests=False,
    )
    b = build_cursor_extension_removal_report(
        monorepo=REPO,
        run_vscode_compile=False,
        run_vscode_tests=False,
    )
    assert a.to_dict() == b.to_dict()
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    from verification.cursor_extension_removal.reporting import write_verification_outputs

    pa, _ = write_verification_outputs(a, out_a)
    pb, _ = write_verification_outputs(b, out_b)
    assert pa.read_bytes() == pb.read_bytes()


def test_runner_writes_report(tmp_path: Path) -> None:
    report = run_cursor_extension_removal_verification(
        monorepo=REPO,
        output_dir=tmp_path,
        write_report=True,
        run_vscode_compile=False,
        run_vscode_tests=False,
        check_determinism_pair=True,
    )
    path = tmp_path / "cursor-extension-removal-verification.json"
    assert path.is_file()
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert '"schema_name": "cursor-extension-removal-verification"' in path.read_text()
    assert "/Users/" not in path.read_text()
