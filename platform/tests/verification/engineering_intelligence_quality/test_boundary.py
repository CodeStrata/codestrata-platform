"""Boundary tests for SV.12."""

from __future__ import annotations

from pathlib import Path

from verification.engineering_intelligence_quality.contract import default_contract


def test_verification_outside_runtime_package() -> None:
    platform = Path(__file__).resolve().parents[3]
    assert (platform / "verification" / "engineering_intelligence_quality").is_dir()
    assert not (platform / "src" / "codestrata_platform" / "verification").exists() or not (
        platform / "src" / "codestrata_platform" / "verification" / "engineering_intelligence_quality"
    ).exists()


def test_contract_forbids_sv13_and_redesign() -> None:
    c = default_contract()
    assert c.start_sv13 is False
    assert c.redesign_report is False
    assert c.reassess_by_default is False
