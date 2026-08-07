"""Focused tests for Slice 12.10 Epic 12 completion verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.product_cleanup_repository_split_completion.contract import (
    EPIC12_VERIFICATION_SCHEMAS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    TOTAL_SLICES,
)
from verification.product_cleanup_repository_split_completion.runner import (
    build_report,
    run,
)
from verification.product_cleanup_repository_split_completion.slice_matrix import (
    build_slice_matrix,
)

ROOT = Path(__file__).resolve().parents[3]


def test_slice_matrix_ten_packages() -> None:
    matrix, _checks, _defects = build_slice_matrix(ROOT)
    assert len(matrix) == TOTAL_SLICES
    assert set(EPIC12_VERIFICATION_SCHEMAS) == {s.slice_id for s in matrix}
    assert not (ROOT / "cursor-plugin").exists()


def test_cursor_absent() -> None:
    assert not (ROOT / "cursor-plugin").exists()
    inv = (ROOT / "scripts/release/inventory.py").read_text(encoding="utf-8")
    assert "cursor-plugin" not in inv


def test_vscode_version() -> None:
    data = json.loads((ROOT / "vscode-plugin/package.json").read_text(encoding="utf-8"))
    assert data["version"] == "0.2.0"


def test_export_targets_closed() -> None:
    text = (ROOT / "scripts/export_repository.py").read_text(encoding="utf-8")
    assert "community" in text and "infrastructure" in text


def test_ci_workflow_present() -> None:
    wf = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "community-export-verification" in wf
    assert "infrastructure-export-verification" in wf
    assert "vscode-ci" in wf
    assert "aws-actions/configure-aws-credentials" not in wf


def test_epic13_absent() -> None:
    assert not (ROOT / "verification/vscode_extension_completion").exists()
    assert not (ROOT / "verification/epic13").exists()


def test_runner_fast_path() -> None:
    report = build_report(ROOT, rerun_expensive=False, run_vscode_npm=False)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.epic == 12
    assert report.start_epic_13 is False
    assert report.completed_slices == 10
    assert report.failed_checks == 0, [c.name for c in report.checks if not c.ok]
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}


def test_dual_run_deterministic_fast() -> None:
    r1 = run(ROOT, rerun_expensive=False, run_vscode_npm=False)
    r2 = run(ROOT, rerun_expensive=False, run_vscode_npm=False)
    path = (
        ROOT
        / "reports/verification/sv12-10"
        / "product-cleanup-repository-split-completion-verification.json"
    )
    assert path.is_file()
    assert r1.to_dict() == r2.to_dict()
    blob = path.read_text(encoding="utf-8")
    assert "/Users/" not in blob
    assert "AKIA" not in blob
