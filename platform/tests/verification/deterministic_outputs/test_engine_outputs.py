"""Engine output determinism tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from verification.deterministic_outputs.engine_outputs import check_engine_outputs


@pytest.fixture(scope="module")
def monorepo() -> Path:
    return Path(__file__).resolve().parents[4]


def test_engine_outputs(monorepo: Path) -> None:
    if not (monorepo / "engine/reports/verification/sv10/determinism-samples.json").is_file():
        pytest.skip("SV.10 determinism samples missing")
    checks, defects = check_engine_outputs(monorepo)
    assert not defects
    assert all(c.ok for c in checks), [(c.name, c.detail) for c in checks if not c.ok]
