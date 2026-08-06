"""Boundary and Cursor tests."""

from __future__ import annotations

from verification.privacy_first_telemetry.boundaries import check_boundaries
from verification.privacy_first_telemetry.contract import monorepo_root_from_here
from verification.privacy_first_telemetry.vscode_inputs import load_vscode_inventory


def test_boundaries_pass() -> None:
    root = monorepo_root_from_here()
    vscode = load_vscode_inventory(root)
    checks, defects = check_boundaries(root, vscode)
    assert not defects
    assert all(c.ok for c in checks)


def test_cursor_has_no_telemetry() -> None:
    root = monorepo_root_from_here()
    assert not (root / "cursor-plugin" / "src" / "telemetry").exists()
