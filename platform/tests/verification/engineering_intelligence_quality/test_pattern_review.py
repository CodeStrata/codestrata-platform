"""Thin coverage for pattern_review."""

from __future__ import annotations

def test_pattern_review_importable() -> None:
    import verification.engineering_intelligence_quality as pkg
    assert pkg.ENGINEERING_INTELLIGENCE_QUALITY_ID
