"""Additional Technology Distribution validation and edge-case tests."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution import (
    TechnologyDistributionPolicy,
    build_technology_distribution,
    normalize_technology_name,
    technology_id,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution.validation import (
    validate_distribution,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DataVisibility,
    VersionState,
)
from codestrata_platform.intelligence_reporting.domain.technology import (
    Ratio,
    TechnologyDistribution,
    TechnologyDistributionObservation,
    TechnologyVersionObservation,
)
from tests.intelligence_reporting.application.aggregation.conftest import prepare_aggregation
from tests.intelligence_reporting.application.conftest import full_engine_report


def test_policy_rejects_invalid_minimum() -> None:
    with pytest.raises(ValueError):
        TechnologyDistributionPolicy(minimum_repository_count=0)


def test_policy_token_includes_normalization_version() -> None:
    policy = TechnologyDistributionPolicy()
    assert "technology-normalization-v1" in policy.policy_token
    assert policy.policy_token.startswith("technology-distribution:v1:")


def test_minimum_repository_count_filters() -> None:
    _, aggregation, _ = prepare_aggregation()
    full = build_technology_distribution(aggregation)
    filtered = build_technology_distribution(
        aggregation,
        policy=TechnologyDistributionPolicy(minimum_repository_count=99),
    )
    assert full.distribution.observations
    assert filtered.distribution.observations == ()


def test_included_categories_filter() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_technology_distribution(
        aggregation,
        policy=TechnologyDistributionPolicy(included_categories=("language",)),
    )
    assert result.distribution.observations
    assert all(item.category == "language" for item in result.distribution.observations)


def test_fuzzy_matching_not_applied() -> None:
    # Near-miss names must not collapse via edit distance.
    left, _ = normalize_technology_name("Pythn")
    right, _ = normalize_technology_name("Python")
    assert left != right


def test_identity_stable_and_version_independent() -> None:
    assert technology_id(category="language", normalized_name="Python") == (
        technology_id(category="Language", normalized_name="python")
    )
    assert technology_id(category="language", normalized_name="Python") != (
        technology_id(category="framework", normalized_name="Python")
    )


def test_unavailable_version_bucket() -> None:
    report = full_engine_report(
        extra_assessment={
            "technologies": [{"name": "Python", "category": "language"}]
        }
    )
    _, aggregation, _ = prepare_aggregation(
        repos=[("repo:one", "assessment:one", "run:one", report)]
    )
    result = build_technology_distribution(aggregation)
    obs = result.distribution.observations[0]
    assert any(v.state is VersionState.UNAVAILABLE and v.version is None for v in obs.versions)


def test_validation_rejects_duplicate_identity() -> None:
    obs = TechnologyDistributionObservation(
        technology_id="technology:language:python",
        normalized_name="Python",
        category="language",
        repository_count=1,
        repository_ratio=Ratio.of(1, 1),
        occurrence_count=1,
        repository_ids=("repo:one",),
    )
    dist = TechnologyDistribution(
        observations=(obs, obs),
        repository_denominator=1,
    )
    # TechnologyDistribution.__post_init__ keeps both unless we bypass — construct raw
    # via object and validate.
    with pytest.raises(InvalidValueError, match="duplicate"):
        validate_distribution(
            TechnologyDistribution(
                observations=(
                    obs,
                    TechnologyDistributionObservation(
                        technology_id="technology:language:python",
                        normalized_name="Python",
                        category="language",
                        repository_count=1,
                        repository_ratio=Ratio.of(1, 1),
                        occurrence_count=1,
                        repository_ids=("repo:two",),
                    ),
                ),
                repository_denominator=1,
            ),
            dataset_repository_ids={"repo:one", "repo:two"},
            visibility_policy=VisibilityAggregationScope.MIXED_INTERNAL,
            repository_visibility={
                "repo:one": DataVisibility.INTERNAL,
                "repo:two": DataVisibility.INTERNAL,
            },
        )


def test_validation_rejects_private_ref_in_public_scope() -> None:
    dist = TechnologyDistribution(
        observations=(
            TechnologyDistributionObservation(
                technology_id="technology:language:python",
                normalized_name="Python",
                category="language",
                repository_count=1,
                repository_ratio=Ratio.of(1, 1),
                occurrence_count=1,
                repository_ids=("repo:private",),
                confidence=ConfidenceLevel.HIGH,
            ),
        ),
        repository_denominator=1,
    )
    with pytest.raises(InvalidValueError, match="private"):
        validate_distribution(
            dist,
            dataset_repository_ids={"repo:private"},
            visibility_policy=VisibilityAggregationScope.PUBLIC_OSS,
            repository_visibility={"repo:private": DataVisibility.CUSTOMER_PRIVATE},
        )


def test_input_order_invariance() -> None:
    first = full_engine_report(
        extra_assessment={
            "technologies": [
                {"name": "Java", "category": "language", "version": "17"},
                {"name": "Python", "category": "language", "version": "3.11"},
            ]
        }
    )
    second = full_engine_report(
        finding_id="finding:2",
        evidence_id="ev:2",
        recommendation_id="rec:2",
        action_id="pa:2",
        initiative_id="init:2",
        extra_assessment={
            "technologies": [
                {"name": "Python", "category": "language", "version": "3.11"},
                {"name": "Java", "category": "language", "version": "17"},
            ]
        },
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
    left_result = build_technology_distribution(left)
    right_result = build_technology_distribution(right)
    assert [item.technology_id for item in left_result.distribution.observations] == [
        item.technology_id for item in right_result.distribution.observations
    ]


def test_diagnostics_populated() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_technology_distribution(aggregation)
    assert result.diagnostics.input_fact_count >= 1
    assert result.diagnostics.distinct_technology_count >= 1
    assert result.diagnostics.eligible_repository_count >= 1


def test_known_version_requires_value_on_observation() -> None:
    with pytest.raises(InvalidValueError):
        TechnologyVersionObservation(
            version=None,
            state=VersionState.KNOWN,
            repository_ids=("repo:one",),
            occurrence_count=1,
        )
