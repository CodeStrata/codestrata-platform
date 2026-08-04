"""Tests for eir module."""

from __future__ import annotations

from verification.cross_schema_compatibility import eir as mod


def test_module_importable() -> None:
    assert mod is not None
