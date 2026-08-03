"""Dataset limitations, visibility, diagnostics, and EIR integration."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.report_quality import (
    ReportQualityPolicy,
    build_report_quality,
    populate_report_quality,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    LimitationSeverity,
    ReportScope,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    to_stable_dict,
)
from tests.intelligence_reporting.application.aggregation.conftest import prepare_aggregation
from tests.intelligence_reporting.application.report_quality.conftest import (
    prepare_quality_report,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison import (
    populate_report_capability_comparisons,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution import (
    populate_report_technology_distribution,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)


def test_limitation_ids_unique_and_stable() -> None:
    _, aggregation, _, report = prepare_quality_report()
    ids = [item.limitation_id.value for item in report.limitations]
    assert len(ids) == len(set(ids))
    assert all(item.startswith("limitation:") for item in ids)
    again = populate_report_quality(report, aggregation)
    assert [item.limitation_id.value for item in again.limitations] == ids


def test_non_temporal_and_selection_bias_scopes() -> None:
    _, _, _, oss = prepare_quality_report(scope=ReportScope.PUBLIC_OSS_DATASET)
    assert any(item.category.value == "non_temporal_dataset" for item in oss.limitations)
    assert any(item.category.value == "selection_bias" for item in oss.limitations)

    _, _, _, customer = prepare_quality_report(scope=ReportScope.CUSTOMER_PORTFOLIO)
    assert any(item.category.value == "non_temporal_dataset" for item in customer.limitations)
    # Complete customer portfolio does not automatically get OSS selection bias.
    assert not any(
        item.category.value == "selection_bias"
        and "not a random sample" in item.statement
        for item in customer.limitations
    )


def test_internal_validation_selection_or_fixture_disclosure() -> None:
    result, aggregation, _ = prepare_aggregation(
        source_type=SourceType.FIXTURE,
        visibility=DataVisibility.INTERNAL,
    )
    report = EngineeringIntelligenceReport.create(
        title="fixtures",
        report_scope=ReportScope.INTERNAL_VALIDATION_DATASET,
        dataset=result.dataset,
    )
    report = populate_report_technology_distribution(report, aggregation)
    report = populate_report_capability_comparisons(report, aggregation)
    report = populate_report_quality(report, aggregation)
    cats = {item.category.value for item in report.limitations}
    assert "selection_bias" in cats or "controlled_fixture_presence" in cats


def test_public_limitations_exclude_private_ids() -> None:
    _, _, _, report = prepare_quality_report(
        scope=ReportScope.PUBLIC_OSS_DATASET,
        visibility=DataVisibility.PUBLIC,
    )
    for limitation in report.limitations:
        if limitation.customer_visible:
            for repo_id in limitation.affected_repository_ids:
                assert not repo_id.startswith("customer:")


def test_report_integration_preserves_sections() -> None:
    _, _, _, report = prepare_quality_report()
    assert report.technology_distribution.observations or report.technology_distribution.repository_denominator >= 0
    assert report.capability_comparisons
    assert report.assessment_head_distributions
    assert report.confidence.derivation_status.value == "derived"
    assert report.limitations
    assert report.repository_drilldowns == ()
    assert report.methodology.interpretation_policy_bundle_id
    assert report.interpretation_policy_bundle_id


def test_serialization_round_trip_with_bundle() -> None:
    _, _, _, report = prepare_quality_report(scope=ReportScope.PUBLIC_OSS_DATASET)
    payload = to_stable_dict(report)
    assert payload["schema_version"] == "1.0"
    assert payload["interpretation_policy_bundle_id"].startswith("interp-bundle:")
    restored = from_stable_dict(payload)
    assert to_stable_dict(restored) == payload


def test_diagnostics_reconcile() -> None:
    _, aggregation, _, report = prepare_quality_report()
    result = build_report_quality(report, aggregation)
    diag = result.diagnostics
    assert diag.included_repository_count == report.confidence.repository_sample_count
    assert diag.comparable_repository_count == report.confidence.comparable_repository_count
    assert diag.report_confidence_level == report.confidence.level.value
    assert diag.policy_bundle_id == report.interpretation_policy_bundle_id
    assert diag.unresolved_reference_count == 0
    assert diag.limitation_count == len(report.limitations)


def test_severity_vocabulary_is_interpretation_not_finding() -> None:
    _, _, _, report = prepare_quality_report()
    for item in report.limitations:
        assert item.severity in set(LimitationSeverity)
        assert item.severity.value not in {"critical", "high", "medium", "low"}


def test_assessment_age_deferred() -> None:
    policy = ReportQualityPolicy()
    assert "deferred" in policy.assessment_age_policy
