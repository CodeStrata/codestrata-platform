"""Tests for Slice 12.3 Cursor documentation removal."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_documentation_removal.checks import (
    check_extension_docs,
    check_root_readme,
)
from verification.cursor_documentation_removal.contract import SCHEMA_NAME, SCHEMA_VERSION, default_contract
from verification.cursor_documentation_removal.runner import (
    build_report,
    run_cursor_documentation_removal_verification,
)
from verification.cursor_documentation_removal.scenarios import check_scenarios

REPO = Path(__file__).resolve().parents[3]


def test_contract() -> None:
    c = default_contract()
    assert c.schema_name == SCHEMA_NAME == "cursor-documentation-removal-verification"
    assert c.schema_version == SCHEMA_VERSION == "1.0.0"
    assert c.start_slice_12_4 is False


def test_root_and_extension() -> None:
    checks, defects = check_root_readme(REPO)
    assert all(c.ok for c in checks), checks
    assert defects == []
    checks, defects = check_extension_docs(REPO)
    assert all(c.ok for c in checks), [c for c in checks if not c.ok]
    assert defects == []


def test_scenarios() -> None:
    checks, defects = check_scenarios(REPO)
    assert len(checks) >= 26
    assert all(c.ok for c in checks), [c.name for c in checks if not c.ok]
    assert defects == []


def test_build_and_determinism(tmp_path: Path) -> None:
    a = build_report(REPO)
    b = build_report(REPO)
    assert a.to_dict() == b.to_dict()
    assert a.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    report = run_cursor_documentation_removal_verification(
        monorepo=REPO,
        output_dir=tmp_path,
        write_report=True,
        check_determinism_pair=True,
    )
    path = tmp_path / "cursor-documentation-removal-verification.json"
    assert path.is_file()
    assert report.failed_checks == 0
    assert "/Users/" not in path.read_text()
