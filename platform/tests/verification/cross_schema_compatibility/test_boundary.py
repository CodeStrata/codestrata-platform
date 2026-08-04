"""Boundary tests for SV.14."""

from __future__ import annotations

from pathlib import Path

from verification.cross_schema_compatibility.contract import default_contract


def test_package_outside_src() -> None:
    platform = Path(__file__).resolve().parents[3]
    assert (platform / "verification" / "cross_schema_compatibility").is_dir()
    assert not (
        platform / "src" / "codestrata_platform" / "verification" / "cross_schema_compatibility"
    ).exists()


def test_readme_and_no_sv15() -> None:
    c = default_contract()
    assert c.start_sv15 is False
    readme = (
        Path(__file__).resolve().parents[3]
        / "verification"
        / "cross_schema_compatibility"
        / "README.md"
    )
    text = readme.read_text(encoding="utf-8").lower()
    assert "1.0.0" in text
    assert "sv.15" in text
    assert "not started" in text
