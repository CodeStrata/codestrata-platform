"""Assessment compatibility tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from verification.cross_schema_compatibility.artifacts import load_assessment_artifacts
from verification.cross_schema_compatibility.assessment import check_assessment_artifacts


@pytest.fixture(scope="module")
def monorepo() -> Path:
    return Path(__file__).resolve().parents[4]


def test_all_22_assessments(monorepo: Path) -> None:
    if not (monorepo / "engine/reports/verification/sv10/artifacts").is_dir():
        pytest.skip("SV.10 missing")
    checks, failures = check_assessment_artifacts(load_assessment_artifacts(monorepo))
    assert all(c.ok for c in checks), [(c.name, c.detail) for c in checks if not c.ok]
    assert not failures
