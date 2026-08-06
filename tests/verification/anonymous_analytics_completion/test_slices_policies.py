"""Slice matrix, policy, and schema registry tests for Slice 10.9."""

from __future__ import annotations

from verification.anonymous_analytics_completion.contract import monorepo_root_from_here
from verification.anonymous_analytics_completion.inventory import (
    load_engine_inventory,
    load_vscode_analytics_inventory,
)
from verification.anonymous_analytics_completion.policies import (
    EXPECTED_POLICY_COUNT,
    POLICY_REGISTRY,
    check_policies,
)
from verification.anonymous_analytics_completion.schemas import build_schema_registry, check_schemas
from verification.anonymous_analytics_completion.slices import build_slice_matrix


def test_slice_matrix_all_nine_complete() -> None:
    root = monorepo_root_from_here()
    matrix, checks, defects = build_slice_matrix(root)
    assert len(matrix) == 9
    incomplete = [s for s in matrix if s.status != "complete"]
    assert incomplete == [], incomplete
    assert not defects
    assert all(c.ok for c in checks)


def test_policy_registry_deterministic_and_sorted() -> None:
    assert len(POLICY_REGISTRY) == EXPECTED_POLICY_COUNT == 7
    assert list(POLICY_REGISTRY) == sorted(POLICY_REGISTRY)
    assert len(POLICY_REGISTRY) == len(set(POLICY_REGISTRY))
    assert "community-vscode-anonymous-analytics-policy:1.0" in POLICY_REGISTRY


def test_check_policies_pass() -> None:
    root = monorepo_root_from_here()
    engine = load_engine_inventory()
    vscode = load_vscode_analytics_inventory(root)
    checks, defects = check_policies(engine, vscode)
    assert not defects
    assert all(c.ok for c in checks)


def test_schema_registry_and_checks_pass() -> None:
    root = monorepo_root_from_here()
    engine = load_engine_inventory()
    vscode = load_vscode_analytics_inventory(root)
    registry = build_schema_registry()
    assert registry["product.assessment_report_schema"] == "Assessment report:1.2"
    assert registry["engine.telemetry_runtime_event_schema"] == (
        "community-telemetry-runtime-event:1.0"
    )
    checks, defects = check_schemas(engine, vscode)
    assert not defects
    assert all(c.ok for c in checks)
    assert engine.base_schema_urn != vscode.schema_urn
