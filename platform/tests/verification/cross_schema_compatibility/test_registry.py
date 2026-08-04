"""Schema registry tests."""

from __future__ import annotations

from verification.cross_schema_compatibility.registry import (
    build_schema_registry,
    producer_consumer_matrix,
)


def test_registry_includes_expected_contracts() -> None:
    names = {e.contract_name for e in build_schema_registry()}
    for required in (
        "assessment_report",
        "validation_record",
        "validation_summary",
        "engineering_intelligence_report",
        "website_safe_eir_export",
        "community_cloud_api",
        "community_assessment_metadata",
        "system_verification_reports",
    ):
        assert required in names


def test_producer_consumer_matrix_flows() -> None:
    flows = {row["flow"] for row in producer_consumer_matrix()}
    assert "A_engine_assessment" in flows
    assert "G_system_verification_reports" in flows
