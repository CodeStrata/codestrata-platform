"""Thin coverage for technology_review."""

from __future__ import annotations

def test_technology_review_importable() -> None:
    import verification.engineering_intelligence_quality as pkg
    assert pkg.ENGINEERING_INTELLIGENCE_QUALITY_ID
