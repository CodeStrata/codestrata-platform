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
    path = monorepo / "platform/reports/verification/sv12/engineering-intelligence-report.json"
    if not path.is_file():
        pytest.skip("SV.12 EIR missing")
    checks = check_negative_scenarios(load_sv12_eir(monorepo))
    assert all(c.ok for c in checks), [(c.name, c.detail) for c in checks if not c.ok]
