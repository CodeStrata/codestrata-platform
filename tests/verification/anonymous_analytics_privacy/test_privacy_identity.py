"""Privacy / identity / scenario coverage for Slice 10.8."""

from __future__ import annotations

import tempfile
from pathlib import Path

from verification.anonymous_analytics_privacy.contract import monorepo_root_from_here
from verification.anonymous_analytics_privacy.engine_inputs import load_engine_inventory
from verification.anonymous_analytics_privacy.identity import check_identity
from verification.anonymous_analytics_privacy.privacy import check_base_contract
from verification.anonymous_analytics_privacy.scenarios import check_scenarios
from verification.anonymous_analytics_privacy.vscode_inputs import (
    load_vscode_analytics_inventory,
)


def test_base_contract() -> None:
    engine = load_engine_inventory()
    checks, defects = check_base_contract(engine)
    assert not defects
    assert all(c.ok for c in checks)


def test_identity_temp_home() -> None:
    root = monorepo_root_from_here()
    engine = load_engine_inventory()
    vscode = load_vscode_analytics_inventory(root)
    with tempfile.TemporaryDirectory() as tmp:
        checks, defects = check_identity(
            engine, vscode, tmp_home=Path(tmp) / "home"
        )
    assert not defects
    assert all(c.ok for c in checks)


def test_negative_scenarios() -> None:
    vscode = load_vscode_analytics_inventory(monorepo_root_from_here())
    checks, defects = check_scenarios(vscode)
    assert not defects
    assert all(c.ok for c in checks)
