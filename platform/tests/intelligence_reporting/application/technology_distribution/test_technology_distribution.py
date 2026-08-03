"""Technology Distribution insight tests."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution import (
    TechnologyDistributionPolicy,
    build_technology_distribution,
    normalize_technology_name,
    populate_report_technology_distribution,
    technology_id,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    ReportScope,
    SourceType,
    VersionState,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from codestrata_platform.intelligence_reporting.domain.serialization import to_stable_dict
from tests.intelligence_reporting.application.aggregation.conftest import prepare_aggregation
from tests.intelligence_reporting.application.conftest import full_engine_report


def test_normalize_aliases_and_keep_distinct() -> None:
    assert normalize_technology_name("nodejs")[0] == "Node.js"
    assert normalize_technology_name("Node.js")[0] == "Node.js"
    assert normalize_technology_name("javascript")[0] == "JavaScript"
    assert normalize_technology_name("java")[0] == "Java"
    assert normalize_technology_name("java")[0] != normalize_technology_name("javascript")[0]
    assert normalize_technology_name("dotnet")[0] == ".NET"
    assert normalize_technology_name("aspnetcore")[0] == "ASP.NET Core"
    assert normalize_technology_name("npm")[0] == "npm"
    assert normalize_technology_name("nodejs")[0] != normalize_technology_name("npm")[0]
    assert normalize_technology_name("docker")[0] != normalize_technology_name("kubernetes")[0]
    assert normalize_technology_name("SomeUnknownLib")[0] == "SomeUnknownLib"
    assert technology_id(category="language", normalized_name="Java") == (
        "technology:language:java"
    )


def test_build_distribution_presence_vs_occurrence() -> None:
    report = full_engine_report(
        extra_assessment={
            "technologies": [
                {"name": "Python", "category": "language", "version": "3.11", "confidence": "high"},
                {"name": "python", "category": "language", "version": "3.11", "confidence": "high"},
            ]
        }
    )
    _, aggregation, _ = prepare_aggregation(
        repos=[("repo:one", "assessment:one", "run:one", report)]
    )
    result = build_technology_distribution(aggregation)
    python = next(
        item for item in result.distribution.observations if item.normalized_name == "Python"
    )
    assert python.repository_count == 1
    assert python.occurrence_count == 2
    assert python.repository_ratio.numerator == 1
    assert python.repository_ratio.denominator == result.distribution.repository_denominator


def test_multi_repo_distribution_and_ordering() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_technology_distribution(aggregation)
    assert result.distribution.repository_denominator >= 1
    assert len(result.distribution.observations) >= 1
    python = next(
        item for item in result.distribution.observations if item.normalized_name == "Python"
    )
    assert python.repository_count == 2
    assert set(python.repository_ids) == {"repo:one", "repo:two"}
    # Ordering: presence desc
    counts = [item.repository_count for item in result.distribution.observations]
    assert counts == sorted(counts, reverse=True)


def test_conflicting_versions_vs_cross_repo_diversity() -> None:
    conflict = full_engine_report(
        extra_assessment={
            "technologies": [
                {"name": "Python", "category": "language", "version": "3.11"},
                {"name": "Python", "category": "language", "version": "3.12"},
            ]
        }
    )
    diverse_a = full_engine_report(
        extra_assessment={
            "technologies": [{"name": "Python", "category": "language", "version": "3.11"}]
        }
    )
    diverse_b = full_engine_report(
        finding_id="finding:2",
        evidence_id="ev:2",
        recommendation_id="rec:2",
        action_id="pa:2",
        initiative_id="init:2",
        extra_assessment={
            "technologies": [{"name": "Python", "category": "language", "version": "3.12"}]
        },
    )
    _, conflict_agg, _ = prepare_aggregation(
        repos=[("repo:conflict", "assessment:c", "run:c", conflict)]
    )
    conflict_result = build_technology_distribution(conflict_agg)
    conflict_obs = conflict_result.distribution.observations[0]
    assert any(v.state is VersionState.CONFLICTING for v in conflict_obs.versions)

    _, diverse_agg, _ = prepare_aggregation(
        repos=[
            ("repo:a", "assessment:a", "run:a", diverse_a),
            ("repo:b", "assessment:b", "run:b", diverse_b),
        ]
    )
    diverse_result = build_technology_distribution(diverse_agg)
    diverse_obs = next(
        item for item in diverse_result.distribution.observations if item.normalized_name == "Python"
    )
    assert diverse_obs.repository_count == 2
    assert not any(v.state is VersionState.CONFLICTING for v in diverse_obs.versions)


def test_zero_denominator_unavailable_ratio() -> None:
    # Empty eligible set via public policy on anonymized aggregation.
    _, aggregation, _ = prepare_aggregation(visibility=DataVisibility.ANONYMIZED)
    policy = TechnologyDistributionPolicy(
        visibility_policy=VisibilityAggregationScope.PUBLIC_OSS
    )
    result = build_technology_distribution(aggregation, policy=policy)
    assert result.distribution.repository_denominator == 0
    assert result.distribution.observations == ()
    assert any("denominator_unavailable" in item for item in result.distribution.limitations)


def test_public_scope_blocks_private_refs() -> None:
    _, aggregation, _ = prepare_aggregation(
        visibility=DataVisibility.PUBLIC,
        source_type=SourceType.PUBLIC_OSS,
    )
    policy = TechnologyDistributionPolicy(
        visibility_policy=VisibilityAggregationScope.PUBLIC_OSS
    )
    result = build_technology_distribution(aggregation, policy=policy)
    assert result.distribution.observations
    assert all(
        repo.startswith("repo:") for obs in result.distribution.observations for repo in obs.repository_ids
    )


def test_report_integration_populates_only_technology_distribution() -> None:
    ingest_result, aggregation, _ = prepare_aggregation()
    report = EngineeringIntelligenceReport.create(
        title="Tech distribution shell",
        report_scope=ReportScope.INTERNAL_VALIDATION_DATASET,
        dataset=ingest_result.dataset,
        repository_population=aggregation.repository_population,
    )
    populated = populate_report_technology_distribution(report, aggregation)
    assert populated.technology_distribution.observations
    assert populated.capability_comparisons == ()
    assert populated.recurring_patterns == ()
    assert populated.modernization_observations == ()
    assert populated.repository_drilldowns == ()
    payload = to_stable_dict(populated.technology_distribution)
    assert "snippet" not in payload
    assert "source_body" not in payload


def test_determinism_and_policy_change() -> None:
    _, aggregation, _ = prepare_aggregation()
    left = build_technology_distribution(aggregation)
    right = build_technology_distribution(aggregation)
    assert to_stable_dict(left.distribution) == to_stable_dict(right.distribution)
    other = build_technology_distribution(
        aggregation,
        policy=TechnologyDistributionPolicy(policy_version="v2"),
    )
    assert other.policy_token != left.policy_token


def test_category_distributions_present() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_technology_distribution(aggregation)
    assert result.distribution.category_distributions
    language = next(
        item
        for item in result.distribution.category_distributions
        if item.category == "language"
    )
    assert language.technology_count >= 1
    assert language.repository_count >= 1


def test_no_modern_outdated_claims_in_limitations() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_technology_distribution(aggregation)
    blob = " ".join(result.distribution.limitations).lower()
    assert "outdated" not in blob
    assert "is modern" not in blob
    assert "portfolio is modern" not in blob
    assert "industry popularity" in blob
    assert "modernization need" in blob
