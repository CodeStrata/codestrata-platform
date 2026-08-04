"""Thin coverage for dataset_review."""

from __future__ import annotations

def test_dataset_review_importable() -> None:
    import verification.engineering_intelligence_quality as pkg
    assert pkg.ENGINEERING_INTELLIGENCE_QUALITY_ID
