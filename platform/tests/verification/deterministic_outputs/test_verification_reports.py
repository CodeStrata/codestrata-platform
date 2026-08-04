"""Tests for verification_reports."""

from __future__ import annotations

from verification.deterministic_outputs import verification_reports as mod


def test_module_importable() -> None:
    assert mod is not None
