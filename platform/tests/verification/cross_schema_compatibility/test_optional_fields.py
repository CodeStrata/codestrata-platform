"""Tests for optional_fields module."""

from __future__ import annotations

from verification.cross_schema_compatibility import optional_fields as mod


def test_module_importable() -> None:
    assert mod is not None
