"""Retention, encryption, and access reconciliation integration tests."""

from __future__ import annotations

from verification.community_data_lake.infrastructure import check_infrastructure_static

from .assertions import assert_all_ok


def test_retention_encryption_access_reconciliation() -> None:
    assert_all_ok(check_infrastructure_static(), label="infra_static")
