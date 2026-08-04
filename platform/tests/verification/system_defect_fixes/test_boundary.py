"""Boundary tests for SV.13."""

from __future__ import annotations

from pathlib import Path

from verification.system_defect_fixes.contract import default_contract


def test_readme_documents_no_privacy_bypass() -> None:
    readme = (
        Path(__file__).resolve().parents[3]
        / "verification"
        / "system_defect_fixes"
        / "README.md"
    )
    text = readme.read_text(encoding="utf-8").lower()
    assert "fail-closed" in text or "fail closed" in text.replace("-", " ")
    assert "allowlist" in text
    assert "sv.14" in text
    assert "not started" in text


def test_contract_forbids_bypass() -> None:
    c = default_contract()
    assert c.weaken_privacy is False
    assert c.repository_specific_allowlist is False
    assert c.known_issues_bypass is False
    assert c.start_sv14 is False
