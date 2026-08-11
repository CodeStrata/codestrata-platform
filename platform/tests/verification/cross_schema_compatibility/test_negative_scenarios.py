"""Negative scenario tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from verification.cross_schema_compatibility.artifacts import load_sv12_eir
from verification.cross_schema_compatibility.negative_scenarios import (
    check_negative_scenarios,
)


@pytest.fixture(scope="module")
def monorepo() -> Path:
    return Path(__file__).resolve().parents[4]


def test_negative_scenarios(monorepo: Path) -> None:
    # HISTORICAL_FROZEN_CHARACTERIZATION: SV.12/SV.10 frozen slice artifacts.
    # Skip when those inputs are absent rather than gating current main.
    sv10 = monorepo / "engine" / "reports" / "verification" / "sv10"
    if not sv10.is_dir():
        pytest.skip("SV.10 artifacts missing")
    path = monorepo / "platform/reports/verification/sv12/engineering-intelligence-report.json"
    if not path.is_file():
        pytest.skip("SV.12 EIR missing")
    checks = check_negative_scenarios(load_sv12_eir(monorepo))
    assert all(c.ok for c in checks), [(c.name, c.detail) for c in checks if not c.ok]
