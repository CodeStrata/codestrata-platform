"""Core commercial intelligence domain model tests."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.errors import InvalidValueError, InvariantViolationError
from codestrata_platform.intelligence_reporting.domain.capability import (
    AssessmentHeadDistribution,
    CapabilityComparison,
    CapabilityDistribution,
    RepositoryCapabilitySnapshot,
)
from codestrata_platform.intelligence_reporting.domain.confidence import (
    IntelligenceReportConfidence,
)
from codestrata_platform.intelligence_reporting.domain.drilldown import (
    RepositoryIntelligenceDrilldown,
    SafeEntityRef,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ConfidenceLevel,
    CoverageStatus,
    DataVisibility,
    DerivationStatus,
    LimitationCategory,
    LimitationSeverity,
    ModernizationObservationCategory,
    PatternType,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.limitations import DatasetLimitation
from codestrata_platform.intelligence_reporting.domain.modernization import (
    ModernizationObservation,
)
from codestrata_platform.intelligence_reporting.domain.patterns import (
    RecurringIntelligencePattern,
)
from codestrata_platform.intelligence_reporting.domain.technology import (
    Ratio,
    TechnologyDistribution,
    TechnologyDistributionObservation,
)
from tests.intelligence_reporting.domain.conftest import make_dataset, make_ref, make_report


def test_duplicate_repository_rejected() -> None:
    with pytest.raises((InvariantViolationError, InvalidValueError), match="duplicate repository"):
        make_dataset(
            (
                make_ref(
                    repository_id="repo:one",
                    assessment_id="assessment:one",
                    assessment_run_id="run:one",
                ),
                make_ref(
                    repository_id="repo:one",
                    assessment_id="assessment:dup",
                    assessment_run_id="run:dup",
                ),
            )
        )


def test_ratio_zero_denominator_unavailable() -> None:
    from codestrata_platform.intelligence_reporting.domain.enums import RatioStatus

    ratio = Ratio.of(0, 0)
    assert ratio.status is RatioStatus.UNAVAILABLE
    assert ratio.value is None
    with pytest.raises(InvalidValueError):
        Ratio(numerator=1, denominator=0, status=RatioStatus.AVAILABLE)


def test_technology_repository_vs_occurrence_counts() -> None:
    dist = TechnologyDistribution(
        repository_denominator=2,
        observations=(
            TechnologyDistributionObservation(
                technology_id="tech:python",
                normalized_name="Python",
                category="language",
                repository_count=2,
                repository_ratio=Ratio.of(2, 2),
                occurrence_count=3,
                repository_ids=("repo:one", "repo:two"),
                source_assessment_ids=("assessment:one", "assessment:two"),
            ),
        ),
    )
    assert dist.observations[0].occurrence_count > dist.observations[0].repository_count


def test_capability_distribution_no_maturity_score() -> None:
    comparison = CapabilityComparison(
        assessment_head_id="security",
        repositories=(
            RepositoryCapabilitySnapshot(
                repository_id="repo:one",
                assessment_id="assessment:one",
                assessment_head_id="security",
                activation_status=ActivationStatus.ACTIVATED,
                coverage_status=CoverageStatus.COMPLETE,
                confidence_level=ConfidenceLevel.HIGH,
            ),
        ),
        distribution=CapabilityDistribution(complete_count=1, high_confidence_count=1),
    )
    assert not hasattr(comparison, "maturity_score")
    assert comparison.distribution.coverage_total == 1


def test_recurring_pattern_requires_two_repositories() -> None:
    with pytest.raises(InvalidValueError, match="at least two repositories"):
        RecurringIntelligencePattern.create(
            pattern_type=PatternType.RECURRING_RULE,
            title="Credential literals",
            statement="Credential literals recur.",
            repository_ids=("repo:one",),
            rule_ids=("security.credential-literal",),
            assessment_head_ids=("security",),
        )


def test_modernization_observation_requires_support_and_forbids_roi() -> None:
    with pytest.raises(InvalidValueError, match="recommendation or priority-action support"):
        ModernizationObservation.create(
            title="Shared foundation",
            statement="Shared foundation work recurs.",
            category=ModernizationObservationCategory.SHARED_FOUNDATION,
            repository_ids=("repo:one", "repo:two"),
        )
    with pytest.raises(InvalidValueError, match="ROI"):
        ModernizationObservation.create(
            title="Cut cost with high ROI",
            statement="This guarantees ROI.",
            category=ModernizationObservationCategory.SHARED_FOUNDATION,
            repository_ids=("repo:one", "repo:two"),
            recommendation_ids=("rec:1",),
        )


def test_assessment_head_distribution_is_not_a_trend() -> None:
    dist = AssessmentHeadDistribution(
        assessment_head_id="dependency",
        repository_count=2,
        complete_coverage_count=1,
        partial_coverage_count=1,
    )
    assert not hasattr(dist, "time_points")
    assert dist.repository_count == 2


def test_confidence_requires_limitations_when_not_deferred() -> None:
    with pytest.raises(InvalidValueError, match="limitations"):
        IntelligenceReportConfidence(
            level=ConfidenceLevel.LIMITED,
            basis=("sample_size",),
            derivation_status=DerivationStatus.DERIVED,
            limitations=(),
        )


def test_limitation_and_drilldown_belong_to_dataset() -> None:
    report = make_report()
    limitation = DatasetLimitation.create(
        category=LimitationCategory.SAMPLE_SIZE,
        severity=LimitationSeverity.MODERATE,
        statement="Sample size is small.",
        affected_repository_ids=("repo:one",),
    )
    drilldown = RepositoryIntelligenceDrilldown.create(
        repository_id="repo:one",
        assessment_id="assessment:one",
        display_name="Repo One",
        source_type=SourceType.PUBLIC_OSS,
        visibility=DataVisibility.ANONYMIZED,
        finding_refs=(
            SafeEntityRef(
                entity_id="finding:1",
                assessment_id="assessment:one",
                entity_kind="finding",
                label="Finding one",
            ),
        ),
    )
    enriched = make_report(
        report.dataset,
    )
    # Rebuild with limitation + drilldown via create
    from codestrata_platform.intelligence_reporting.domain.report import (
        EngineeringIntelligenceReport,
    )

    built = EngineeringIntelligenceReport.create(
        title=report.title,
        report_scope=report.report_scope,
        dataset=report.dataset,
        limitations=(limitation,),
        repository_drilldowns=(drilldown,),
    )
    assert built.limitations[0].limitation_id.value.startswith("limitation:")
    assert built.repository_drilldowns[0].repository_id == "repo:one"
    _ = enriched


def test_pattern_and_observation_resolve_inside_report() -> None:
    pattern = RecurringIntelligencePattern.create(
        pattern_type=PatternType.RECURRING_RULE,
        title="Missing tests",
        statement="Missing tests recur across repositories.",
        repository_ids=("repo:one", "repo:two"),
        rule_ids=("codestrata-rule-missing-tests",),
        assessment_head_ids=("testing",),
    )
    observation = ModernizationObservation.create(
        title="Establish test baselines",
        statement="Test baseline actions recur across the dataset.",
        category=ModernizationObservationCategory.TESTING_ENABLEMENT,
        repository_ids=("repo:one", "repo:two"),
        recommendation_ids=("rec:tests-one", "rec:tests-two"),
        supporting_finding_ids=("finding:tests-one", "finding:tests-two"),
    )
    from codestrata_platform.intelligence_reporting.domain.report import (
        EngineeringIntelligenceReport,
    )

    report = EngineeringIntelligenceReport.create(
        title="Pattern report",
        report_scope=make_report().report_scope,
        dataset=make_dataset(),
        recurring_patterns=(pattern,),
        modernization_observations=(observation,),
    )
    assert len(report.recurring_patterns) == 1
    assert len(report.modernization_observations) == 1
