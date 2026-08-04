"""SV.11 / SV.12 regression and boundary tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from verification.system_defect_fixes.contract import default_contract
from verification.system_defect_fixes.sv11_regression import check_sv11_ei_ready


@pytest.fixture(scope="module")
def monorepo() -> Path:
    return Path(__file__).resolve().parents[4]


def test_sv11_ei_ready_uses_platform(monorepo: Path) -> None:
    sv10 = monorepo / "engine" / "reports" / "verification" / "sv10" / "artifacts"
    if not sv10.is_dir():
        pytest.skip("SV.10 artifacts not present")
    result = check_sv11_ei_ready(monorepo)
    assert result.ok, result.detail


def test_boundary_no_sv14_no_bypass() -> None:
    c = default_contract()
    assert c.start_sv14 is False
    assert c.weaken_privacy is False
    assert c.repository_specific_allowlist is False
    assert c.known_issues_bypass is False


def test_package_outside_src() -> None:
    platform = Path(__file__).resolve().parents[3]
    assert (platform / "verification" / "system_defect_fixes").is_dir()
    assert not (
        platform / "src" / "codestrata_platform" / "verification" / "system_defect_fixes"
    ).exists()
