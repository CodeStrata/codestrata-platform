"""Tests for evidence-backed portfolio modernization observations."""

from __future__ import annotations

import pytest

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison import (
    populate_report_capability_comparisons,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations import (
    ModernizationObservationPolicy,
    build_modernization_observations,
    populate_report_modernization_observations,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns import (
    build_recurring_patterns,
    populate_report_recurring_patterns,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution import (
    populate_report_technology_distribution,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DataVisibility,
    ModernizationObservationCategory,
    ReportScope,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import build_observation_id
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from codestrata_platform.intelligence_reporting.domain.serialization import to_stable_dict
from tests.intelligence_reporting.application.aggregation.conftest import prepare_aggregation
from tests.intelligence_reporting.application.conftest import full_engine_report


def test_policy_rejects_one_repository_portfolio() -> None:
    with pytest.raises(ValueError):
        ModernizationObservationPolicy(minimum_repository_count=1)
    with pytest.raises(ValueError):
        ModernizationObservationPolicy(allow_single_repository=True)
    policy = ModernizationObservationPolicy()
    assert policy.policy_token.startswith("modernization-observations:v1:")


def test_recommendation_backed_observation_across_two_repos() -> None:
    _, aggregation, _ = prepare_aggregation()
    patterns = build_recurring_patterns(aggregation).patterns
    result = build_modernization_observations(
        aggregation, recurring_patterns=patterns
    )
    assert result.observations
    security = next(
        item
        for item in result.observations
        if item.category is ModernizationObservationCategory.SECURITY_REMEDIATION
    )
    assert security.repository_count == 2
    assert set(security.repository_ids) == {"repo:one", "repo:two"}
    assert security.recommendation_ids
    assert security.priority_action_ids
    assert security.supporting_finding_ids
    assert security.supporting_evidence_ids
    assert security.normalized_subject.startswith("modernization-action:")
    assert "actions were produced" in security.statement
    assert "must" not in security.statement.lower()
    assert "roi" not in security.statement.lower()
    assert not hasattr(security, "portfolio_recommendation")
    assert security.confidence in {
        ConfidenceLevel.HIGH,
        ConfidenceLevel.MODERATE,
        ConfidenceLevel.LIMITED,
    }


def test_one_repository_does_not_create_observation() -> None:
    report = full_engine_report()
    _, aggregation, _ = prepare_aggregation(
        repos=[("repo:one", "assessment:one", "run:one", report)]
    )
    result = build_modernization_observations(aggregation)
    assert result.observations == ()
    assert result.diagnostics.below_threshold_count >= 1


def test_title_change_does_not_alter_action_identity() -> None:
    left = full_engine_report()
    right = full_engine_report(
        finding_id="finding:2",
        evidence_id="ev:2",
        recommendation_id="rec:2",
        action_id="pa:2",
        initiative_id="init:2",
        extra_assessment={
            "deterministic_recommendations": [
                {
                    "id": "rec:2",
                    "title": "Completely different title wording",
                    "summary": "Different prose",
                    "priority": "low",
                    "category": "security",
                    "supporting_finding_ids": ["finding:2"],
                    "related_finding_ids": ["finding:2"],
                    "primary_finding_id": "finding:2",
                    "recommendation_type": "remediation",
                    "evidence_completeness": "complete",
                    "limitations": [],
                }
            ]
        },
    )
    _, aggregation, _ = prepare_aggregation(
        repos=[
            ("repo:a", "assessment:a", "run:a", left),
            ("repo:b", "assessment:b", "run:b", right),
        ]
    )
    result = build_modernization_observations(aggregation)
    assert len(result.observations) >= 1
    subjects = {item.normalized_subject for item in result.observations}
    assert any(
        subject.startswith("modernization-action:") and ":security:" in subject
        for subject in subjects
    )

def test_pattern_without_recommendation_does_not_create_observation() -> None:
    # Findings recur but no recommendations → no modernization observation.
    left = full_engine_report(
        extra_assessment={
            "deterministic_recommendations": [],
            "priority_actions": [],
            "roadmap": {"initiatives": []},
        }
    )
    right = full_engine_report(
        finding_id="finding:2",
        evidence_id="ev:2",
        recommendation_id="rec:2",
        action_id="pa:2",
        initiative_id="init:2",
        extra_assessment={
            "deterministic_recommendations": [],
            "priority_actions": [],
            "roadmap": {"initiatives": []},
        },
    )
    _, aggregation, _ = prepare_aggregation(
        repos=[
            ("repo:a", "assessment:a", "run:a", left),
            ("repo:b", "assessment:b", "run:b", right),
        ]
    )
    patterns = build_recurring_patterns(aggregation).patterns
    assert patterns  # rule may still recur
    result = build_modernization_observations(
        aggregation, recurring_patterns=patterns
    )
    assert result.observations == ()


def test_technology_prevalence_alone_creates_no_observation() -> None:
    # Default tech is Python without recommendations of technology category.
    _, aggregation, _ = prepare_aggregation()
    result = build_modernization_observations(aggregation)
    assert not any(
        "technology" in item.normalized_subject for item in result.observations
    )
    assert not any(
        item.category is ModernizationObservationCategory.OTHER
        and "python" in item.title.lower()
        for item in result.observations
    )


def test_public_scope_excludes_anonymized() -> None:
    _, aggregation, _ = prepare_aggregation(visibility=DataVisibility.ANONYMIZED)
    result = build_modernization_observations(
        aggregation,
        policy=ModernizationObservationPolicy(
            visibility_policy=VisibilityAggregationScope.PUBLIC_OSS
        ),
    )
    assert result.observations == ()


def test_identity_includes_membership_per_slice_61() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_modernization_observations(aggregation)
    observation = result.observations[0]
    rebuilt = build_observation_id(
        category=observation.category.value,
        normalized_subject=observation.normalized_subject,
        repository_ids=observation.repository_ids,
        recommendation_ids=observation.recommendation_ids,
        priority_action_ids=observation.priority_action_ids,
        policy_version=observation.policy_version,
    )
    assert rebuilt.value == observation.observation_id.value


def test_report_integration_preserves_prior_sections() -> None:
    ingest_result, aggregation, _ = prepare_aggregation()
    report = EngineeringIntelligenceReport.create(
        title="Modernization shell",
        report_scope=ReportScope.INTERNAL_VALIDATION_DATASET,
        dataset=ingest_result.dataset,
        repository_population=aggregation.repository_population,
    )
    with_tech = populate_report_technology_distribution(report, aggregation)
    with_cap = populate_report_capability_comparisons(with_tech, aggregation)
    with_patterns = populate_report_recurring_patterns(with_cap, aggregation)
    populated = populate_report_modernization_observations(with_patterns, aggregation)
    assert populated.modernization_observations
    assert populated.technology_distribution.observations
    assert populated.capability_comparisons
    assert populated.recurring_patterns
    assert populated.repository_drilldowns == ()
    assert populated.confidence.derivation_status.value in {"deferred", "unavailable"}


def test_determinism() -> None:
    _, aggregation, _ = prepare_aggregation()
    left = build_modernization_observations(aggregation)
    right = build_modernization_observations(aggregation)
    assert to_stable_dict(left.observations) == to_stable_dict(right.observations)
    other = build_modernization_observations(
        aggregation,
        policy=ModernizationObservationPolicy(policy_version="v2"),
    )
    assert other.policy_token != left.policy_token


def test_included_categories_filter() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_modernization_observations(
        aggregation,
        policy=ModernizationObservationPolicy(
            included_categories=(ModernizationObservationCategory.DEPENDENCY_GOVERNANCE,)
        ),
    )
    assert result.observations == ()
