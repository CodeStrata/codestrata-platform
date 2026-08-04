"""Tests for roundtrip."""

from __future__ import annotations

from verification.deterministic_outputs import roundtrip as mod


def test_module_importable() -> None:
    assert mod is not None
