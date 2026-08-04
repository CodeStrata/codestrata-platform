"""Artifact loader tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from verification.cross_schema_compatibility.artifacts import (
    catalog_release_validation_count,
    load_assessment_artifacts,
)
from verification.cross_schema_compatibility.contract import TARGET_REPOSITORY_COUNT


@pytest.fixture(scope="module")
def monorepo() -> Path:
    return Path(__file__).resolve().parents[4]


def test_catalog_and_artifacts(monorepo: Path) -> None:
    sv10 = monorepo / "engine" / "reports" / "verification" / "sv10" / "artifacts"
    if not sv10.is_dir():
        pytest.skip("SV.10 artifacts missing")
    assert catalog_release_validation_count(monorepo) == TARGET_REPOSITORY_COUNT
    artifacts = load_assessment_artifacts(monorepo)
    assert len(artifacts) == TARGET_REPOSITORY_COUNT
