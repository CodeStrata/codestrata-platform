"""Tests for validation_outputs."""

from __future__ import annotations

from verification.deterministic_outputs import validation_outputs as mod


def test_module_importable() -> None:
    assert mod is not None
