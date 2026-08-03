"""Drill-down policy and identity tests."""

from __future__ import annotations

import pytest

from codestrata_platform.intelligence_reporting.application.report_quality.policy import (
    build_interpretation_policy_bundle_id,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns import (
    RepositoryDrilldownPolicy,
    populate_report_repository_drilldowns,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import build_drilldown_id
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from tests.intelligence_reporting.application.repository_drilldowns.conftest import (
    prepare_drilldown_report,
)


def test_policy_token_stable_and_bounded() -> None:
    left = RepositoryDrilldownPolicy().policy_token
    right = RepositoryDrilldownPolicy().policy_token
    assert left == right
    assert left.startswith("repository-drilldowns:v1:")


def test_unbounded_policy_rejected() -> None:
    with pytest.raises(ValueError, match="must be >= 1"):
        RepositoryDrilldownPolicy(maximum_finding_refs=0)


def test_policy_participates_in_bundle() -> None:
    base = dict(
        technology_policy_token="t",
        capability_policy_token="c",
        recurring_pattern_policy_token="p",
        modernization_policy_token="m",
        report_quality_policy_token="q",
        repository_drilldown_policy_token="d1",
    )
    left = build_interpretation_policy_bundle_id(**base)
    right = build_interpretation_policy_bundle_id(
        **{**base, "repository_drilldown_policy_token": "d2"}
    )
    assert left != right


def test_drilldown_id_stable_and_policy_sensitive() -> None:
    left = build_drilldown_id(
        repository_id="repo:one",
        assessment_id="assessment:one",
        assessment_run_id="run:one",
        dataset_id="dataset:abc",
        canonical_report_digest="digest1",
        policy_token="policy-a",
    )
    right = build_drilldown_id(
        repository_id="repo:one",
        assessment_id="assessment:one",
        assessment_run_id="run:one",
        dataset_id="dataset:abc",
        canonical_report_digest="digest1",
        policy_token="policy-a",
    )
    assert left.value == right.value
    changed_policy = build_drilldown_id(
        repository_id="repo:one",
        assessment_id="assessment:one",
        assessment_run_id="run:one",
        dataset_id="dataset:abc",
        canonical_report_digest="digest1",
        policy_token="policy-b",
    )
    assert changed_policy.value != left.value
    changed_assessment = build_drilldown_id(
        repository_id="repo:one",
        assessment_id="assessment:other",
        assessment_run_id="run:one",
        dataset_id="dataset:abc",
        canonical_report_digest="digest1",
        policy_token="policy-a",
    )
    assert changed_assessment.value != left.value
    changed_digest = build_drilldown_id(
        repository_id="repo:one",
        assessment_id="assessment:one",
        assessment_run_id="run:one",
        dataset_id="dataset:abc",
        canonical_report_digest="digest2",
        policy_token="policy-a",
    )
    assert changed_digest.value != left.value


def test_display_name_does_not_change_id() -> None:
    _, aggregation, _, report = prepare_drilldown_report()
    first = report.repository_drilldowns[0]
    # Rebuild with same policy — ID stable regardless of display presentation.
    rebuilt = populate_report_repository_drilldowns(report, aggregation)
    assert rebuilt.repository_drilldowns[0].drilldown_id.value == first.drilldown_id.value


def test_changed_drilldown_policy_changes_report_id() -> None:
    result, aggregation, _, report = prepare_drilldown_report()
    original = report.report_id.value
    base = EngineeringIntelligenceReport.create(
        title=report.title,
        report_scope=report.report_scope,
        dataset=result.dataset,
        technology_distribution=report.technology_distribution,
        capability_comparisons=report.capability_comparisons,
        recurring_patterns=report.recurring_patterns,
        assessment_head_distributions=report.assessment_head_distributions,
        modernization_observations=report.modernization_observations,
        confidence=report.confidence,
        limitations=report.limitations,
    )
    from codestrata_platform.intelligence_reporting.application.report_quality import (
        populate_report_quality,
    )

    altered_policy = RepositoryDrilldownPolicy(maximum_finding_refs=5)
    with_quality = populate_report_quality(
        base, aggregation, repository_drilldown_policy=altered_policy
    )
    altered = populate_report_repository_drilldowns(
        with_quality, aggregation, policy=altered_policy
    )
    assert altered.interpretation_policy_bundle_id != report.interpretation_policy_bundle_id
    assert altered.report_id.value != original
