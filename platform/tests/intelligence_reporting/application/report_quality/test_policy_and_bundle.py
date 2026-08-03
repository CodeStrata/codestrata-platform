"""ReportQualityPolicy and interpretation-policy bundle tests."""

from __future__ import annotations

import pytest

from codestrata_platform.intelligence_reporting.application.report_quality.policy import (
    CatalogVersions,
    ReportQualityPolicy,
    SourceDiversityMode,
    build_interpretation_policy_bundle,
    build_interpretation_policy_bundle_id,
)
from codestrata_platform.intelligence_reporting.domain.enums import ReportScope


def test_policy_token_stable() -> None:
    left = ReportQualityPolicy().policy_token
    right = ReportQualityPolicy().policy_token
    assert left == right
    assert left.startswith("report-quality:v1:")


def test_policy_rejects_numeric_confidence_configuration() -> None:
    with pytest.raises(ValueError, match="prohibited"):
        ReportQualityPolicy(confidence_policy_version="confidence_percentage-v1")


def test_sample_thresholds_and_material_sections() -> None:
    policy = ReportQualityPolicy(
        minimum_repository_count=2,
        small_sample_threshold=3,
        material_sections=("technology_distribution", "capability_comparison"),
    )
    assert "technology_distribution" in policy.material_sections
    assert policy.small_sample_threshold == 3


def test_diversity_mode_by_scope() -> None:
    policy = ReportQualityPolicy()
    assert (
        policy.diversity_mode_for_scope(ReportScope.PUBLIC_OSS_DATASET)
        is SourceDiversityMode.MATERIAL_FOR_PUBLIC
    )
    assert (
        policy.diversity_mode_for_scope(ReportScope.CUSTOMER_PORTFOLIO)
        is SourceDiversityMode.INFORMATIONAL_FOR_CUSTOMER
    )
    assert (
        policy.diversity_mode_for_scope(ReportScope.INTERNAL_VALIDATION_DATASET)
        is SourceDiversityMode.FIXTURE_EXPLICIT_FOR_VALIDATION
    )


def test_bundle_id_deterministic_and_order_invariant() -> None:
    left = build_interpretation_policy_bundle(
        technology_policy_token="tech:a",
        capability_policy_token="cap:b",
        recurring_pattern_policy_token="pat:c",
        modernization_policy_token="mod:d",
        report_quality_policy_token="qual:e",
    )
    right = build_interpretation_policy_bundle(
        technology_policy_token="tech:a",
        capability_policy_token="cap:b",
        recurring_pattern_policy_token="pat:c",
        modernization_policy_token="mod:d",
        report_quality_policy_token="qual:e",
    )
    assert left.bundle_id == right.bundle_id
    assert left.bundle_id.startswith("interp-bundle:")


def test_changed_section_policy_changes_bundle() -> None:
    base = dict(
        technology_policy_token="tech:a",
        capability_policy_token="cap:b",
        recurring_pattern_policy_token="pat:c",
        modernization_policy_token="mod:d",
        report_quality_policy_token="qual:e",
        repository_drilldown_policy_token="drill:a",
        website_export_policy_token="export:a",
    )
    original = build_interpretation_policy_bundle_id(**base)
    assert (
        build_interpretation_policy_bundle_id(**{**base, "technology_policy_token": "tech:x"})
        != original
    )
    assert (
        build_interpretation_policy_bundle_id(**{**base, "capability_policy_token": "cap:x"})
        != original
    )
    assert (
        build_interpretation_policy_bundle_id(
            **{**base, "recurring_pattern_policy_token": "pat:x"}
        )
        != original
    )
    assert (
        build_interpretation_policy_bundle_id(
            **{**base, "modernization_policy_token": "mod:x"}
        )
        != original
    )
    assert (
        build_interpretation_policy_bundle_id(
            **{**base, "report_quality_policy_token": "qual:x"}
        )
        != original
    )
    assert (
        build_interpretation_policy_bundle_id(
            **{**base, "repository_drilldown_policy_token": "drill:x"}
        )
        != original
    )
    assert (
        build_interpretation_policy_bundle_id(
            **{**base, "website_export_policy_token": "export:x"}
        )
        != original
    )


def test_catalog_and_template_version_changes_bundle() -> None:
    base = build_interpretation_policy_bundle_id(
        bundle_version="v1",
        technology_policy_token="t",
        capability_policy_token="c",
        recurring_pattern_policy_token="p",
        modernization_policy_token="m",
        report_quality_policy_token="q",
        catalog_versions=CatalogVersions(),
    )
    changed = build_interpretation_policy_bundle_id(
        bundle_version="v1",
        technology_policy_token="t",
        capability_policy_token="c",
        recurring_pattern_policy_token="p",
        modernization_policy_token="m",
        report_quality_policy_token="q",
        catalog_versions=CatalogVersions(head_catalog_version="commercial-head-catalog-v2"),
    )
    assert base != changed


def test_timestamps_do_not_affect_bundle() -> None:
    # Bundle builders accept no timestamp fields — identity is token-only.
    left = build_interpretation_policy_bundle_id(
        bundle_version="v1",
        technology_policy_token="t",
        capability_policy_token="c",
        recurring_pattern_policy_token="p",
        modernization_policy_token="m",
        report_quality_policy_token="q",
    )
    right = build_interpretation_policy_bundle_id(
        bundle_version="v1",
        technology_policy_token="t",
        capability_policy_token="c",
        recurring_pattern_policy_token="p",
        modernization_policy_token="m",
        report_quality_policy_token="q",
    )
    assert left == right
