"""Slice matrix and version registry tests."""

from __future__ import annotations

from verification.privacy_first_telemetry_completion.contract import monorepo_root_from_here
from verification.privacy_first_telemetry_completion.slices import build_slice_matrix
from verification.privacy_first_telemetry_completion.versions import check_versions


def test_slice_matrix_complete() -> None:
    matrix, checks, defects = build_slice_matrix(monorepo_root_from_here())
    assert len(matrix) == 15
    assert not defects
    assert all(s.status == "complete" for s in matrix)
    assert all(c.ok for c in checks)


def test_version_registries() -> None:
    policies, schemas, verification, checks, defects = check_versions()
    assert not defects
    assert all(c.ok for c in checks)
    assert schemas["product.assessment_schema"] == "1.2"
    assert schemas["engine.runtime_event_schema_version"] == "1.0"
    assert verification["completion_verification"] == "1.0.0"
    assert len(policies) == 13
