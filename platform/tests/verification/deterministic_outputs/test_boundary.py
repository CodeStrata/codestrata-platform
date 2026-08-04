"""Boundary tests for SV.15."""

from __future__ import annotations

from pathlib import Path

from verification.deterministic_outputs.contract import default_contract


def test_package_outside_src() -> None:
    platform = Path(__file__).resolve().parents[3]
    assert (platform / "verification" / "deterministic_outputs").is_dir()
    assert not (
        platform
        / "src"
        / "codestrata_platform"
        / "verification"
        / "deterministic_outputs"
    ).exists()


def test_readme_no_sv16() -> None:
    c = default_contract()
    assert c.start_sv16 is False
    readme = (
        Path(__file__).resolve().parents[3]
        / "verification"
        / "deterministic_outputs"
        / "README.md"
    )
    text = readme.read_text(encoding="utf-8").lower()
    assert "sv.16" in text
    assert "not started" in text
    assert "1.0.0" in text
