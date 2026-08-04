"""Tests for website_export."""

from __future__ import annotations

from verification.deterministic_outputs import website_export as mod


def test_module_importable() -> None:
    assert mod is not None
