"""Tests for capability and assessment-head comparison."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison import (
    COMMERCIAL_HEAD_CATALOG,
    CapabilityComparisonPolicy,
    build_capability_comparisons,
    canonicalize_assessment_head,
    populate_report_capability_comparisons,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution import (
    build_technology_distribution,
    populate_report_technology_distribution,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ConfidenceLevel,
    CoverageStatus,
    DataVisibility,
    ReportScope,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    to_stable_dict,
)
from tests.intelligence_reporting.application.aggregation.conftest import prepare_aggregation
from tests.intelligence_reporting.application.conftest import full_engine_report


def test_policy_identity_and_rejects_ranking_config() -> None:
    policy = CapabilityComparisonPolicy()
    assert policy.policy_token.startswith("capability-comparison:v1:")
    with pytest.raises(ValueError):
        CapabilityComparisonPolicy(count_presentation_policy="maturity_score_ranking")
    with pytest.raises(ValueError):
        CapabilityComparisonPolicy(minimum_comparable_repository_count=0)


def test_head_catalog_aliases_and_order() -> None:
    assert canonicalize_assessment_head("security") == "security_intelligence"
    assert canonicalize_assessment_head("security_intelligence") == "security_intelligence"
    with pytest.raises(InvalidValueError):
        canonicalize_assessment_head("not-a-real-head")
    assert "security_intelligence" in COMMERCIAL_HEAD_CATALOG
    assert len(COMMERCIAL_HEAD_CATALOG) == len(set(COMMERCIAL_HEAD_CATALOG))


def test_build_comparisons_preserves_activation_coverage_confidence() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_capability_comparisons(aggregation)
    security = next(
        item
        for item in result.comparisons
        if item.assessment_head_id == "security_intelligence"
    )
    assert len(security.repositories) == 2
    for snap in security.repositories:
        assert snap.activation_status is ActivationStatus.ACTIVATED
        assert snap.coverage_status is CoverageStatus.COMPLETE
        assert snap.confidence_level is ConfidenceLevel.HIGH
        assert snap.finding_count == 1
        assert snap.recommendation_count == 1
        assert snap.priority_action_count == 1
        assert snap.highest_severity == "high"
    assert security.distribution.complete_count == 2
    assert security.distribution.high_confidence_count == 2
    assert not hasattr(security, "maturity_score")

    dependency = next(
        item
        for item in result.comparisons
        if item.assessment_head_id == "dependency_intelligence"
    )
    assert all(snap.activation_status is ActivationStatus.DISABLED for snap in dependency.repositories)
    assert all(snap.coverage_status is CoverageStatus.DISABLED for snap in dependency.repositories)

    cloud = next(
        item for item in result.comparisons if item.assessment_head_id == "cloud_readiness"
    )
    assert all(
        snap.coverage_status is CoverageStatus.UNAVAILABLE for snap in cloud.repositories
    )


def test_zero_findings_not_healthy_and_no_ranking() -> None:
    report = full_engine_report(
        extra_assessment={
            "findings": [],
            "deterministic_recommendations": [],
            "priority_actions": [],
            "roadmap": {"initiatives": []},
            "finding_correlations": [],
            "assessment_coverage": {
                "security_intelligence": {"status": "complete"},
            },
            "assessment_head_confidence": {
                "security_intelligence": {"level": "high"},
            },
        }
    )
    _, aggregation, _ = prepare_aggregation(
        repos=[("repo:one", "assessment:one", "run:one", report)]
    )
    result = build_capability_comparisons(
        aggregation,
        policy=CapabilityComparisonPolicy(
            included_assessment_heads=("security_intelligence",)
        ),
    )
    security = result.comparisons[0]
    assert security.assessment_head_id == "security_intelligence"
    snap = security.repositories[0]
    assert snap.finding_count == 0
    assert snap.coverage_status is CoverageStatus.COMPLETE
    assert snap.highest_severity is None
    assert any("zero_findings" in item for item in snap.limitations)
    blob = " ".join(security.limitations).lower()
    assert "do not rank" in blob
    assert "best repository" not in blob
    assert "worst repository" not in blob


def test_included_heads_filter() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_capability_comparisons(
        aggregation,
        policy=CapabilityComparisonPolicy(
            included_assessment_heads=("security_intelligence",)
        ),
    )
    assert [item.assessment_head_id for item in result.comparisons] == [
        "security_intelligence"
    ]


def test_head_distributions_reconcile() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_capability_comparisons(aggregation)
    security = next(
        item
        for item in result.head_distributions
        if item.assessment_head_id == "security_intelligence"
    )
    assert security.repository_count == 2
    assert security.activated_count == 2
    assert security.complete_coverage_count == 2
    assert security.finding_count == 2
    assert security.repositories_with_findings_count == 2
    assert ("high", 2) in security.severity_distribution
    assert ("high", 2) in security.confidence_distribution
    assert not hasattr(security, "time_points")
    assert not hasattr(security, "trend")


def test_public_scope_visibility() -> None:
    _, aggregation, _ = prepare_aggregation(
        visibility=DataVisibility.PUBLIC,
        source_type=SourceType.PUBLIC_OSS,
    )
    result = build_capability_comparisons(
        aggregation,
        policy=CapabilityComparisonPolicy(
            visibility_policy=VisibilityAggregationScope.PUBLIC_OSS,
            included_assessment_heads=("security_intelligence",),
        ),
    )
    assert result.comparisons[0].repositories
    assert all(
        snap.repository_id.startswith("repo:")
        for snap in result.comparisons[0].repositories
    )


def test_public_scope_excludes_anonymized() -> None:
    _, aggregation, _ = prepare_aggregation(visibility=DataVisibility.ANONYMIZED)
    result = build_capability_comparisons(
        aggregation,
        policy=CapabilityComparisonPolicy(
            visibility_policy=VisibilityAggregationScope.PUBLIC_OSS,
            included_assessment_heads=("security_intelligence",),
        ),
    )
    assert result.comparisons[0].repositories == ()
    assert any("denominator_unavailable" in item for item in result.comparisons[0].limitations)


def test_report_integration_preserves_technology_distribution() -> None:
    ingest_result, aggregation, _ = prepare_aggregation()
    tech = build_technology_distribution(aggregation)
    report = EngineeringIntelligenceReport.create(
        title="Capability shell",
        report_scope=ReportScope.INTERNAL_VALIDATION_DATASET,
        dataset=ingest_result.dataset,
        repository_population=aggregation.repository_population,
        technology_distribution=tech.distribution,
    )
    populated = populate_report_capability_comparisons(report, aggregation)
    assert populated.capability_comparisons
    assert populated.assessment_head_distributions
    assert populated.technology_distribution.observations == tech.distribution.observations
    assert populated.recurring_patterns == ()
    assert populated.modernization_observations == ()
    assert populated.repository_drilldowns == ()
    payload = to_stable_dict(populated)
    restored = from_stable_dict(payload)
    assert len(restored.capability_comparisons) == len(populated.capability_comparisons)


def test_determinism_and_policy_change() -> None:
    _, aggregation, _ = prepare_aggregation()
    left = build_capability_comparisons(aggregation)
    right = build_capability_comparisons(aggregation)
    assert to_stable_dict(left.comparisons) == to_stable_dict(right.comparisons)
    other = build_capability_comparisons(
        aggregation,
        policy=CapabilityComparisonPolicy(policy_version="v2"),
    )
    assert other.policy_token != left.policy_token


def test_input_order_invariance() -> None:
    first = full_engine_report()
    second = full_engine_report(
        finding_id="finding:2",
        evidence_id="ev:2",
        recommendation_id="rec:2",
        action_id="pa:2",
        initiative_id="init:2",
    )
    _, left, _ = prepare_aggregation(
        repos=[
            ("repo:a", "assessment:a", "run:a", first),
            ("repo:b", "assessment:b", "run:b", second),
        ]
    )
    _, right, _ = prepare_aggregation(
        repos=[
            ("repo:b", "assessment:b", "run:b", second),
            ("repo:a", "assessment:a", "run:a", first),
        ]
    )
    assert to_stable_dict(build_capability_comparisons(left).comparisons) == to_stable_dict(
        build_capability_comparisons(right).comparisons
    )


def test_tech_then_capability_populate_chain() -> None:
    ingest_result, aggregation, _ = prepare_aggregation()
    report = EngineeringIntelligenceReport.create(
        title="Chain",
        report_scope=ReportScope.INTERNAL_VALIDATION_DATASET,
        dataset=ingest_result.dataset,
        repository_population=aggregation.repository_population,
    )
    with_tech = populate_report_technology_distribution(report, aggregation)
    with_both = populate_report_capability_comparisons(with_tech, aggregation)
    assert with_both.technology_distribution.observations
    assert with_both.capability_comparisons
    assert with_both.assessment_head_distributions
