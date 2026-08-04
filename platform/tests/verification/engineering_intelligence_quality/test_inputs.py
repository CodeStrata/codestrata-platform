"""Thin coverage for inputs."""

from __future__ import annotations

def test_inputs_importable() -> None:
    import verification.engineering_intelligence_quality as pkg
    assert pkg.ENGINEERING_INTELLIGENCE_QUALITY_ID
