"""Contract/schema tests for Slice 10.8."""

from __future__ import annotations

from verification.anonymous_analytics_privacy.contract import monorepo_root_from_here
from verification.anonymous_analytics_privacy.engine_inputs import load_engine_inventory
from verification.anonymous_analytics_privacy.schemas import check_schemas
from verification.anonymous_analytics_privacy.vscode_inputs import (
    load_vscode_analytics_inventory,
)


def test_schema_tokens() -> None:
    root = monorepo_root_from_here()
    engine = load_engine_inventory()
    vscode = load_vscode_analytics_inventory(root)
    checks, defects = check_schemas(engine, vscode)
    assert not defects
    assert all(c.ok for c in checks)
    assert engine.base_schema_urn != vscode.schema_urn
