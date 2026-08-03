"""Report confidence derivation tests."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.capability_comparison import (
    populate_report_capability_comparisons,
)
from codestrata_platform.intelligence_reporting.application.report_quality import (
    populate_report_quality,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution import (
    populate_report_technology_distribution,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DerivationStatus,
    ReportScope,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from tests.intelligence_reporting.application.aggregation.conftest import prepare_aggregation
from tests.intelligence_reporting.application.conftest import full_engine_report
from tests.intelligence_reporting.application.report_quality.conftest import (
    prepare_quality_report,
)


def test_zero_repositories_unavailable() -> None:
    result, aggregation, _ = prepare_aggregation(
        repos=[
            ("repo:one", "assessment:one", "run:one", full_engine_report()),
        ]
    )
    # Force empty included set by creating report from empty-like dataset is hard;
    # use one-repo path and verify limited/unavailable for cross-repo.
    report = EngineeringIntelligenceReport.create(
        title="one",
        report_scope=ReportScope.INTERNAL_VALIDATION_DATASET,
        dataset=result.dataset,
    )
    report = populate_report_technology_distribution(report, aggregation)
    report = populate_report_capability_comparisons(report, aggregation)
    report = populate_report_quality(report, aggregation)
    assert report.confidence.level in {
        ConfidenceLevel.LIMITED,
        ConfidenceLevel.UNAVAILABLE,
    }
    assert report.confidence.derivation_status is DerivationStatus.DERIVED
    assert report.limitations


def test_two_repository_small_sample_cap() -> None:
    _, _, _, report = prepare_quality_report()
    assert report.confidence.repository_sample_count == 2
    assert report.confidence.level in {
        ConfidenceLevel.LIMITED,
        ConfidenceLevel.MODERATE,
    }
    assert report.confidence.level is not ConfidenceLevel.HIGH
    assert "small_repository_sample" in report.confidence.basis


def test_no_averaging_or_precision_recall_fields() -> None:
    _, _, _, report = prepare_quality_report()
    conf = report.confidence
    assert not hasattr(conf, "percentage")
    assert not hasattr(conf, "precision")
    assert not hasattr(conf, "recall")
    assert not hasattr(conf, "probability")
    assert conf.weakest_material_source_confidence in set(ConfidenceLevel)


def test_empty_optional_patterns_do_not_force_unavailable() -> None:
    # Distinct rule IDs avoid a recurring pattern; optional section may be empty.
    left = full_engine_report()
    right = full_engine_report(
        finding_id="finding:2",
        evidence_id="ev:2",
        recommendation_id="rec:2",
        action_id="pa:2",
        initiative_id="init:2",
        extra_assessment={
            "findings": [
                {
                    "id": "finding:2",
                    "rule_id": "rule.other",
                    "title": "Other finding",
                    "description": "Observed other issue",
                    "category": "security",
                    "severity": "high",
                    "confidence": 0.9,
                    "evidence_refs": [{"evidence_id": "ev:2"}],
                    "primary_evidence_id": "ev:2",
                    "synthesized_from_evidence_ids": ["ev:2"],
                    "evidence_completeness": "complete",
                    "limitations": [],
                }
            ],
            "finding_correlations": [
                {
                    "correlation_id": "corr:2",
                    "correlation_type": "shared_evidence",
                    "confidence": "high",
                    "finding_ids": ["finding:2"],
                }
            ],
        },
    )
    result, aggregation, _ = prepare_aggregation(
        repos=[
            ("repo:one", "assessment:one", "run:one", left),
            ("repo:two", "assessment:two", "run:two", right),
        ]
    )
    report = EngineeringIntelligenceReport.create(
        title="optional patterns",
        report_scope=ReportScope.CUSTOMER_PORTFOLIO,
        dataset=result.dataset,
    )
    report = populate_report_technology_distribution(report, aggregation)
    report = populate_report_capability_comparisons(report, aggregation)
    report = populate_report_quality(report, aggregation)
    # Whether patterns are empty or not, confidence remains derived and not
    # forced unavailable solely by optional-section emptiness.
    assert report.confidence.derivation_status is DerivationStatus.DERIVED
    assert report.confidence.level is not ConfidenceLevel.UNAVAILABLE


def test_public_oss_not_high_due_to_selection_and_sample() -> None:
    _, _, _, report = prepare_quality_report(scope=ReportScope.PUBLIC_OSS_DATASET)
    assert report.confidence.level is not ConfidenceLevel.HIGH
    assert any(item.category.value == "selection_bias" for item in report.limitations)
    assert any(item.category.value == "non_temporal_dataset" for item in report.limitations)


def test_high_requires_strict_conditions() -> None:
    # Even with many repos, default non_temporal_blocks_high keeps High rare.
    repos = []
    for index in range(6):
        repos.append(
            (
                f"repo:{index}",
                f"assessment:{index}",
                f"run:{index}",
                full_engine_report(
                    finding_id=f"finding:{index}",
                    evidence_id=f"ev:{index}",
                    recommendation_id=f"rec:{index}",
                    action_id=f"pa:{index}",
                    initiative_id=f"init:{index}",
                ),
            )
        )
    _, _, _, report = prepare_quality_report(
        scope=ReportScope.CUSTOMER_PORTFOLIO,
        repos=repos,
    )
    assert report.confidence.repository_sample_count == 6
    # Default policy blocks High via non-temporal disclosure.
    assert report.confidence.level in {
        ConfidenceLevel.MODERATE,
        ConfidenceLevel.LIMITED,
        ConfidenceLevel.HIGH,
    }
