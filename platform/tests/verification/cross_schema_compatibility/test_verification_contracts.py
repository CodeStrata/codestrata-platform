"""Tests for verification_contracts module."""

from __future__ import annotations

from verification.cross_schema_compatibility import verification_contracts as mod


def test_module_importable() -> None:
    assert mod is not None
