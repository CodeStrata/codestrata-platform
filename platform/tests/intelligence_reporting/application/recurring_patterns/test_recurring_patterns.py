"""Tests for recurring evidence-backed patterns."""

from __future__ import annotations

import pytest

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison import (
    populate_report_capability_comparisons,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns import (
    RecurringPatternPolicy,
    build_recurring_patterns,
    populate_report_recurring_patterns,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution import (
    populate_report_technology_distribution,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DataVisibility,
    PatternType,
    ReportScope,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import build_pattern_id
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from codestrata_platform.intelligence_reporting.domain.serialization import to_stable_dict
from tests.intelligence_reporting.application.aggregation.conftest import prepare_aggregation
from tests.intelligence_reporting.application.conftest import full_engine_report


def test_policy_rejects_single_repository_recurrence() -> None:
    with pytest.raises(ValueError):
        RecurringPatternPolicy(minimum_repository_count=1)
    with pytest.raises(ValueError):
        RecurringPatternPolicy(allow_single_repository=True)
    policy = RecurringPatternPolicy()
    assert "recurring-patterns:v1:" in policy.policy_token


def test_same_rule_across_two_repos_creates_pattern() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_recurring_patterns(aggregation)
    rule_patterns = [
        item
        for item in result.patterns
        if item.pattern_type is PatternType.RECURRING_RULE
        and "rule.demo" in item.rule_ids
    ]
    assert len(rule_patterns) == 1
    pattern = rule_patterns[0]
    assert pattern.repository_count == 2
    assert set(pattern.repository_ids) == {"repo:one", "repo:two"}
    assert pattern.repository_ratio is not None
    assert pattern.repository_ratio.numerator == 2
    assert "`rule.demo`" in pattern.statement
    assert "systemic" not in pattern.statement.lower()
    assert pattern.confidence in {
        ConfidenceLevel.HIGH,
        ConfidenceLevel.MODERATE,
        ConfidenceLevel.LIMITED,
    }


def _finding(
    *,
    finding_id: str,
    rule_id: str,
    category: str,
    evidence_id: str,
    severity: str = "high",
) -> dict:
    return {
        "id": finding_id,
        "rule_id": rule_id,
        "title": f"Finding {finding_id}",
        "description": "Observed issue",
        "category": category,
        "severity": severity,
        "confidence": 0.9,
        "evidence_refs": [{"evidence_id": evidence_id}],
        "primary_evidence_id": evidence_id,
        "synthesized_from_evidence_ids": [evidence_id],
        "evidence_completeness": "complete",
        "limitations": [],
    }


def test_same_rule_many_times_one_repo_not_recurring() -> None:
    report = full_engine_report(
        finding_id="finding:a",
        extra_assessment={
            "findings": [
                _finding(
                    finding_id="finding:a",
                    rule_id="rule.demo",
                    category="security",
                    evidence_id="ev:alpha",
                ),
                _finding(
                    finding_id="finding:b",
                    rule_id="rule.demo",
                    category="security",
                    evidence_id="ev:alpha",
                ),
            ],
            "finding_correlations": [],
        },
    )
    _, aggregation, _ = prepare_aggregation(
        repos=[("repo:one", "assessment:one", "run:one", report)]
    )
    result = build_recurring_patterns(aggregation)
    assert not any("rule.demo" in item.rule_ids for item in result.patterns)
    assert result.diagnostics.finding_occurrence_count >= 1
    assert result.diagnostics.below_threshold_count >= 1


def test_different_rules_remain_separate() -> None:
    left = full_engine_report(
        finding_id="finding:1",
        extra_assessment={
            "findings": [
                _finding(
                    finding_id="finding:1",
                    rule_id="security.credential-literal",
                    category="security",
                    evidence_id="ev:alpha",
                )
            ],
            "finding_correlations": [],
        },
    )
    right = full_engine_report(
        finding_id="finding:2",
        evidence_id="ev:2",
        recommendation_id="rec:2",
        action_id="pa:2",
        initiative_id="init:2",
        extra_assessment={
            "findings": [
                _finding(
                    finding_id="finding:2",
                    rule_id="dependency.mutable-version",
                    category="dependency",
                    evidence_id="ev:2",
                    severity="medium",
                )
            ],
            "finding_correlations": [],
            "assessment_coverage": {
                "dependency_intelligence": {"status": "complete"},
                "security_intelligence": {"status": "complete"},
            },
            "assessment_head_confidence": {
                "dependency_intelligence": {"level": "high"},
                "security_intelligence": {"level": "high"},
            },
        },
    )
    _, aggregation, _ = prepare_aggregation(
        repos=[
            ("repo:a", "assessment:a", "run:a", left),
            ("repo:b", "assessment:b", "run:b", right),
        ]
    )
    result = build_recurring_patterns(aggregation)
    assert not any(
        "security.credential-literal" in item.rule_ids for item in result.patterns
    )
    assert not any(
        "dependency.mutable-version" in item.rule_ids for item in result.patterns
    )


def test_configuration_and_dependency_pattern_types() -> None:
    left = full_engine_report(
        finding_id="finding:1",
        extra_assessment={
            "findings": [
                _finding(
                    finding_id="finding:1",
                    rule_id="security.credential-literal",
                    category="security",
                    evidence_id="ev:alpha",
                ),
                _finding(
                    finding_id="finding:d1",
                    rule_id="dependency.mutable-version",
                    category="dependency",
                    evidence_id="ev:alpha",
                    severity="medium",
                ),
            ],
            "finding_correlations": [],
            "assessment_coverage": {
                "security_intelligence": {"status": "complete"},
                "dependency_intelligence": {"status": "complete"},
            },
            "assessment_head_confidence": {
                "security_intelligence": {"level": "high"},
                "dependency_intelligence": {"level": "high"},
            },
        },
    )
    right = full_engine_report(
        finding_id="finding:2",
        evidence_id="ev:2",
        recommendation_id="rec:2",
        action_id="pa:2",
        initiative_id="init:2",
        extra_assessment={
            "findings": [
                _finding(
                    finding_id="finding:2",
                    rule_id="security.credential-literal",
                    category="security",
                    evidence_id="ev:2",
                ),
                _finding(
                    finding_id="finding:d2",
                    rule_id="dependency.mutable-version",
                    category="dependency",
                    evidence_id="ev:2",
                    severity="medium",
                ),
            ],
            "finding_correlations": [],
            "assessment_coverage": {
                "security_intelligence": {"status": "complete"},
                "dependency_intelligence": {"status": "complete"},
            },
            "assessment_head_confidence": {
                "security_intelligence": {"level": "high"},
                "dependency_intelligence": {"level": "high"},
            },
        },
    )
    _, aggregation, _ = prepare_aggregation(
        repos=[
            ("repo:a", "assessment:a", "run:a", left),
            ("repo:b", "assessment:b", "run:b", right),
        ]
    )
    result = build_recurring_patterns(aggregation)
    types = {item.pattern_type for item in result.patterns}
    assert PatternType.RECURRING_CONFIGURATION_CONDITION in types
    assert PatternType.RECURRING_DEPENDENCY_CONDITION in types


def test_recommendation_pattern_not_title_based() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_recurring_patterns(aggregation)
    rec_patterns = [
        item
        for item in result.patterns
        if item.pattern_type is PatternType.RECURRING_RECOMMENDATION
    ]
    assert rec_patterns
    pattern = rec_patterns[0]
    assert pattern.normalized_subject.startswith("recommendation:")
    assert "Fix demo" not in pattern.normalized_subject
    assert pattern.recommendation_ids


def test_priority_action_patterns_deferred() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_recurring_patterns(aggregation)
    assert not any(
        item.pattern_type is PatternType.RECURRING_PRIORITY_ACTION
        for item in result.patterns
    )
    assert result.diagnostics.priority_action_occurrence_count >= 2


def test_technology_prevalence_not_duplicated_as_pattern() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_recurring_patterns(aggregation)
    assert not any(
        item.pattern_type is PatternType.RECURRING_TECHNOLOGY_CONDITION
        for item in result.patterns
    )


def test_technology_conflict_pattern_across_repos() -> None:
    left = full_engine_report(
        extra_assessment={
            "technologies": [
                {"name": "Python", "category": "language", "version": "3.11"},
                {"name": "Python", "category": "language", "version": "3.12"},
            ]
        }
    )
    right = full_engine_report(
        finding_id="finding:2",
        evidence_id="ev:2",
        recommendation_id="rec:2",
        action_id="pa:2",
        initiative_id="init:2",
        extra_assessment={
            "technologies": [
                {"name": "Python", "category": "language", "version": "3.10"},
                {"name": "Python", "category": "language", "version": "3.11"},
            ]
        },
    )
    _, aggregation, _ = prepare_aggregation(
        repos=[
            ("repo:a", "assessment:a", "run:a", left),
            ("repo:b", "assessment:b", "run:b", right),
        ]
    )
    result = build_recurring_patterns(aggregation)
    tech = [
        item
        for item in result.patterns
        if item.pattern_type is PatternType.RECURRING_TECHNOLOGY_CONDITION
    ]
    assert tech
    assert tech[0].repository_count == 2


def test_identity_includes_repository_membership() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_recurring_patterns(aggregation)
    pattern = next(item for item in result.patterns if "rule.demo" in item.rule_ids)
    rebuilt = build_pattern_id(
        pattern_type=pattern.pattern_type.value,
        normalized_subject=pattern.normalized_subject,
        rule_ids=pattern.rule_ids,
        assessment_head_ids=pattern.assessment_head_ids,
        repository_ids=pattern.repository_ids,
        policy_version=pattern.policy_version,
    )
    assert rebuilt.value == pattern.pattern_id.value
    # Different repo set → different ID
    other = build_pattern_id(
        pattern_type=pattern.pattern_type.value,
        normalized_subject=pattern.normalized_subject,
        rule_ids=pattern.rule_ids,
        assessment_head_ids=pattern.assessment_head_ids,
        repository_ids=("repo:one", "repo:two", "repo:three"),
        policy_version=pattern.policy_version,
    )
    assert other.value != pattern.pattern_id.value


def test_public_scope_excludes_anonymized() -> None:
    _, aggregation, _ = prepare_aggregation(visibility=DataVisibility.ANONYMIZED)
    result = build_recurring_patterns(
        aggregation,
        policy=RecurringPatternPolicy(
            visibility_policy=VisibilityAggregationScope.PUBLIC_OSS
        ),
    )
    assert result.patterns == ()


def test_report_integration_preserves_prior_sections() -> None:
    ingest_result, aggregation, _ = prepare_aggregation()
    report = EngineeringIntelligenceReport.create(
        title="Patterns shell",
        report_scope=ReportScope.INTERNAL_VALIDATION_DATASET,
        dataset=ingest_result.dataset,
        repository_population=aggregation.repository_population,
    )
    with_tech = populate_report_technology_distribution(report, aggregation)
    with_cap = populate_report_capability_comparisons(with_tech, aggregation)
    populated = populate_report_recurring_patterns(with_cap, aggregation)
    assert populated.recurring_patterns
    assert populated.technology_distribution.observations
    assert populated.capability_comparisons
    assert populated.assessment_head_distributions
    assert populated.modernization_observations == ()
    assert populated.repository_drilldowns == ()


def test_determinism() -> None:
    _, aggregation, _ = prepare_aggregation()
    left = build_recurring_patterns(aggregation)
    right = build_recurring_patterns(aggregation)
    assert to_stable_dict(left.patterns) == to_stable_dict(right.patterns)
    other = build_recurring_patterns(
        aggregation,
        policy=RecurringPatternPolicy(policy_version="v2"),
    )
    assert other.policy_token != left.policy_token


def test_included_types_filter() -> None:
    _, aggregation, _ = prepare_aggregation()
    result = build_recurring_patterns(
        aggregation,
        policy=RecurringPatternPolicy(
            included_pattern_types=(PatternType.RECURRING_RULE,)
        ),
    )
    assert result.patterns
    assert all(item.pattern_type is PatternType.RECURRING_RULE for item in result.patterns)
