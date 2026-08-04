"""Ingestion compatibility for previously rejected repositories."""

from __future__ import annotations

from pathlib import Path

import pytest

from verification.system_defect_fixes.ingestion_compatibility import (
    check_three_repository_ingestion,
    classify_affected_reports,
)


@pytest.fixture(scope="module")
def monorepo() -> Path:
    return Path(__file__).resolve().parents[4]


def test_classification_shapes(monorepo: Path) -> None:
    sv10 = monorepo / "engine" / "reports" / "verification" / "sv10" / "artifacts"
    if not sv10.is_dir():
        pytest.skip("SV.10 artifacts not present")
    rows = classify_affected_reports(monorepo)
    assert len(rows) == 3
    for row in rows:
        assert row["classification"] == "A_engine_unsafe_canonical_serialization"
        assert row["finding"] is not None
        assert row["finding"]["rule_id"] == "SEC002"
        assert "pem_header" in row["finding"]["description_shape"]


def test_three_repository_ingestion(monorepo: Path) -> None:
    sv10 = monorepo / "engine" / "reports" / "verification" / "sv10" / "artifacts"
    if not sv10.is_dir():
        pytest.skip("SV.10 artifacts not present")
    checks = check_three_repository_ingestion(monorepo)
    assert checks
    assert all(c.ok for c in checks)
