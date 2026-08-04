"""Integration: build/review 22-repo EIR when SV.10/SV.11 artifacts exist."""

from __future__ import annotations

from pathlib import Path

import pytest

from verification.engineering_intelligence.catalog import monorepo_root_from_here


def test_sv12_full_quality_review() -> None:
    root = monorepo_root_from_here()
    sv10 = root / "engine" / "reports" / "verification" / "sv10" / "curated-repository-validation.json"
    sv11 = root / "engine" / "reports" / "verification" / "sv11" / "assessment-consistency-verification.json"
    if not sv10.is_file() or not sv11.is_file():
        pytest.skip("SV.10/SV.11 artifacts not present")
    from verification.engineering_intelligence_quality.runner import (
        run_engineering_intelligence_quality,
    )

    report = run_engineering_intelligence_quality(monorepo=root)
    assert report.repository_count == 22
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    out = root / "platform" / "reports" / "verification" / "sv12"
    assert (out / "engineering-intelligence-report.json").is_file()
    assert (out / "engineering-intelligence-quality-review.json").is_file()
    # Never touch demo
    demo = root / "platform" / "demo" / "engineering-intelligence-report.json"
    assert demo.is_file()
