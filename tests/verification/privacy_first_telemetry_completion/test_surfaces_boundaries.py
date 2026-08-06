"""Surface, boundary, and scenario tests."""

from __future__ import annotations

from verification.privacy_first_telemetry_completion.boundaries import (
    check_boundaries,
    check_epic10_absence,
)
from verification.privacy_first_telemetry_completion.cli_surface import (
    check_cli_surface,
    check_vscode_surface,
)
from verification.privacy_first_telemetry_completion.contract import monorepo_root_from_here
from verification.privacy_first_telemetry_completion.scenarios import check_scenarios


def test_cli_surface() -> None:
    checks, defects = check_cli_surface(monorepo_root_from_here())
    assert not defects
    assert all(c.ok for c in checks)


def test_vscode_surface() -> None:
    checks, defects = check_vscode_surface(monorepo_root_from_here())
    assert not defects
    assert all(c.ok for c in checks)


def test_boundaries_and_cursor() -> None:
    root = monorepo_root_from_here()
    checks, defects, statuses = check_boundaries(root)
    assert not defects
    assert all(c.ok for c in checks)
    assert statuses["cursor_boundary_status"] == "pass"
    status, e10_checks, e10_defects = check_epic10_absence(root)
    assert status == "pass"
    assert not e10_defects
    assert all(c.ok for c in e10_checks)
    assert not (root / "cursor-plugin" / "src" / "telemetry").exists()


def test_scenarios() -> None:
    checks, defects = check_scenarios(monorepo_root_from_here())
    assert not defects
    assert all(c.ok for c in checks)
    assert len(checks) >= 26
