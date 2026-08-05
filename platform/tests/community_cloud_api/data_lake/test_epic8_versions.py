"""Epic 8 version registry tests (Slice 8.15)."""

from __future__ import annotations

from verification.community_data_lake_completion.versions import (
    build_product_contract_versions,
    build_verification_contract_versions,
    check_versions,
)


def test_product_contract_versions_present() -> None:
    product = build_product_contract_versions()
    assert product["data_lake_policy"] == "1.0"
    assert product["assessment_report"] == "1.2"
    assert product["rate_limit_policy"] == "1.1"
    assert product["community_cloud_api"] == "1.0"
    assert product["eir"] == "1.0"
    assert product["website_export"] == "1.0"


def test_verification_contract_versions_namespace() -> None:
    verification = build_verification_contract_versions()
    assert verification["community_data_lake_integration"] == "1.0.0"
    assert verification["community_data_lake_completion"] == "1.0.0"


def test_version_checks_pass() -> None:
    failures = [item for item in check_versions() if not item.ok]
    assert failures == []
