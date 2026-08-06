"""Negative scenario and boundary tests for Slice 10.9."""

from __future__ import annotations

from verification.anonymous_analytics_completion.boundaries import (
    check_boundaries,
    check_epic11_absence,
)
from verification.anonymous_analytics_completion.contract import monorepo_root_from_here
from verification.anonymous_analytics_completion.inventory import (
    load_engine_inventory,
    load_vscode_analytics_inventory,
)
from verification.anonymous_analytics_completion.scenarios import check_scenarios


def test_epic11_absence() -> None:
    root = monorepo_root_from_here()
    status, checks, defects = check_epic11_absence(root)
    assert status == "pass"
    assert not defects
    assert all(c.ok for c in checks)


def test_boundaries_pass() -> None:
    root = monorepo_root_from_here()
    vscode = load_vscode_analytics_inventory(root)
    checks, defects, statuses = check_boundaries(root, vscode)
    assert not defects
    assert all(c.ok for c in checks)
    assert statuses["platform_boundary_status"] == "pass"
    assert statuses["data_lake_boundary_status"] == "pass"
    assert statuses["cursor_boundary_status"] == "pass"


def test_negative_scenarios_pass() -> None:
    root = monorepo_root_from_here()
    engine = load_engine_inventory()
    vscode = load_vscode_analytics_inventory(root)
    checks, defects = check_scenarios(root, engine, vscode)
    assert not defects
    assert all(c.ok for c in checks)
    assert len(checks) >= 20
