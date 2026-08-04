"""Volatility registry tests."""

from __future__ import annotations

from codestrata.reporting.contract.constants import VOLATILE_JSON_PATHS
from verification.deterministic_outputs.volatility import (
    FORBIDDEN_ENVIRONMENT_FIELDS,
    approved_volatile_fields,
    build_deterministic_contract_registry,
)


def test_approved_volatile_includes_contract_paths() -> None:
    paths = {f.field_path for f in approved_volatile_fields()}
    for path in VOLATILE_JSON_PATHS:
        assert path in paths
        field = next(f for f in approved_volatile_fields() if f.field_path == path)
        assert field.participates_in_ids is False


def test_forbidden_and_registry() -> None:
    assert "home directory" in FORBIDDEN_ENVIRONMENT_FIELDS
    names = {e["contract_name"] for e in build_deterministic_contract_registry()}
    assert "report.json" in names
    assert "website_safe_export" in names
