"""Tests for Slice 12.4 Community client boundary cleanup verification."""

from __future__ import annotations

from pathlib import Path

from verification.community_client_boundary_cleanup.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.community_client_boundary_cleanup.determinism import report_digest
from verification.community_client_boundary_cleanup.runner import (
    build_report,
    run_community_client_boundary_cleanup_verification,
)


def test_build_report_contract() -> None:
    report = build_report(monorepo_root_from_here())
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert "cursor_extension" not in report.active_client_inventory
    assert "vscode_extension" in report.active_client_inventory
    assert "codestrata_cli" in report.active_client_inventory
    assert report.retired_client_inventory == ["cursor_extension"]
    assert report.migration_required is False
    assert report.rewrite_required is False
    assert report.schema_compatibility_decision.startswith("approach_a")


def test_runner_twice_byte_identical(tmp_path: Path) -> None:
    root = monorepo_root_from_here()
    a_dir = tmp_path / "a"
    b_dir = tmp_path / "b"
    a = run_community_client_boundary_cleanup_verification(output_dir=a_dir, monorepo=root)
    b = run_community_client_boundary_cleanup_verification(output_dir=b_dir, monorepo=root)
    assert a.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert b.verdict == a.verdict
    assert report_digest(a) == report_digest(b)
    ja = (a_dir / "community-client-boundary-cleanup-verification.json").read_bytes()
    jb = (b_dir / "community-client-boundary-cleanup-verification.json").read_bytes()
    assert ja == jb
