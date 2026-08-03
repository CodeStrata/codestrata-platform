"""Cross-repository aggregation foundation tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

from codestrata_platform.intelligence_reporting.application.aggregation import (
    DenominatorScope,
    IntelligenceAggregationPolicy,
    LegacyAssessmentPolicy,
    VisibilityAggregationScope,
    aggregate_intelligence_dataset,
    build_aggregation_id,
)
from codestrata_platform.intelligence_reporting.application.aggregation.denominators import (
    build_denominator,
)
from codestrata_platform.intelligence_reporting.application.errors import (
    AggregationUnresolvedReferenceError,
    AggregationVisibilityError,
)
from codestrata_platform.intelligence_reporting.application.ingestion import (
    ingest_assessment_dataset,
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
from codestrata_platform.intelligence_reporting.domain.technology import Ratio
from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)
from tests.intelligence_reporting.application.aggregation.conftest import prepare_aggregation
from tests.intelligence_reporting.application.conftest import (
    full_engine_report,
    legacy_flat_report,
)
from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentDatasetInput,
)


def test_policy_token_stable() -> None:
    policy = IntelligenceAggregationPolicy()
    assert policy.policy_token == "intelligence-aggregation:v1"
    with pytest.raises(ValueError):
        IntelligenceAggregationPolicy(minimum_pattern_repository_count=0)


def test_aggregation_id_stable_and_order_invariant() -> None:
    _, left, _ = prepare_aggregation()
    _, right, _ = prepare_aggregation()
    assert left.aggregation_id == right.aggregation_id
    assert left.aggregation_id.startswith("aggregation:")


def test_changed_policy_changes_aggregation_id() -> None:
    _, base, _ = prepare_aggregation()
    _, other, _ = prepare_aggregation(
        policy=IntelligenceAggregationPolicy(policy_version="v2")
    )
    assert base.aggregation_id != other.aggregation_id


def test_changed_digest_changes_aggregation_id() -> None:
    mutated = full_engine_report()
    mutated["assessment"]["findings"][0]["title"] = "Changed title"
    _, left, _ = prepare_aggregation()
    _, right, _ = prepare_aggregation(
        repos=[
            ("repo:one", "assessment:one", "run:one", mutated),
            (
                "repo:two",
                "assessment:two",
                "run:two",
                full_engine_report(
                    finding_id="finding:2",
                    evidence_id="ev:beta",
                    recommendation_id="rec:2",
                    action_id="pa:2",
                    initiative_id="init:2",
                ),
            ),
        ]
    )
    assert left.aggregation_id != right.aggregation_id


def test_build_aggregation_id_ignores_input_order() -> None:
    left = build_aggregation_id(
        dataset_id="dataset:abc",
        policy_token="intelligence-aggregation:v1",
        digests=["bbb", "aaa"],
        repository_ids=["repo:b", "repo:a"],
        assessment_run_ids=["run:b", "run:a"],
    )
    right = build_aggregation_id(
        dataset_id="dataset:abc",
        policy_token="intelligence-aggregation:v1",
        digests=["aaa", "bbb"],
        repository_ids=["repo:a", "repo:b"],
        assessment_run_ids=["run:a", "run:b"],
    )
    assert left == right


def test_repository_index_one_per_included() -> None:
    _, aggregation, _ = prepare_aggregation()
    assert len(aggregation.repository_index) == 2
    assert aggregation.aggregate_counts.repository_count == 2
    assert aggregation.repository_population.repository_count == 2
    ids = [item.repository_id for item in aggregation.repository_index]
    assert ids == sorted(set(ids))
    assert all(item.canonical_report_reference for item in aggregation.repository_index)


def test_entity_ids_remain_distinct_across_repositories() -> None:
    report_a = full_engine_report(finding_id="finding:shared")
    report_b = full_engine_report(
        finding_id="finding:shared",
        evidence_id="ev:shared",
        recommendation_id="rec:shared",
        action_id="pa:shared",
        initiative_id="init:shared",
    )
    _, aggregation, _ = prepare_aggregation(
        repos=[
            ("repo:a", "assessment:a", "run:a", report_a),
            ("repo:b", "assessment:b", "run:b", report_b),
        ]
    )
    finding_keys = {
        (item.repository_id, item.assessment_id, item.finding_id)
        for item in aggregation.finding_facts
    }
    assert ("repo:a", "assessment:a", "finding:shared") in finding_keys
    assert ("repo:b", "assessment:b", "finding:shared") in finding_keys
    assert len(finding_keys) == 2


def test_denominators_zero_unavailable() -> None:
    denom = build_denominator(
        denominator_id="denom:empty",
        scope=DenominatorScope.COMPARABLE_REPOSITORIES,
        eligible=(),
        numerator=0,
    )
    assert denom.denominator_count == 0
    assert denom.ratio is not None
    assert denom.ratio.value is None
    assert "zero_denominator_unavailable" in denom.limitations


def test_no_percentage_averaging_ratio_from_counts() -> None:
    ratio = Ratio.of(1, 2)
    assert ratio.value == "0.5000"
    # Never average stored percentages — foundation only exposes count ratios.


def test_population_and_technology_facts() -> None:
    report = full_engine_report()
    _, aggregation, _ = prepare_aggregation(
        repos=[
            ("repo:one", "assessment:one", "run:one", report),
            (
                "repo:two",
                "assessment:two",
                "run:two",
                full_engine_report(
                    finding_id="finding:2",
                    evidence_id="ev:2",
                    recommendation_id="rec:2",
                    action_id="pa:2",
                    initiative_id="init:2",
                ),
            ),
        ]
    )
    assert aggregation.repository_population.source_type_counts["public_oss"] == 2
    assert aggregation.aggregate_counts.technology_occurrence_count >= 2
    assert aggregation.aggregate_counts.technology_repository_presence_count == 2
    assert all(item.normalized_name == "Python" for item in aggregation.technology_facts)


def test_assessment_head_facts_preserve_states() -> None:
    _, aggregation, _ = prepare_aggregation()
    security = [
        item
        for item in aggregation.assessment_head_facts
        if item.assessment_head_id == "security_intelligence" and item.repository_id == "repo:one"
    ]
    assert len(security) == 1
    assert security[0].finding_count == 1
    dependency = [
        item
        for item in aggregation.assessment_head_facts
        if item.assessment_head_id == "dependency_intelligence" and item.repository_id == "repo:one"
    ]
    assert dependency[0].activation_status.value == "disabled"
    cloud = [
        item
        for item in aggregation.assessment_head_facts
        if item.assessment_head_id == "cloud_readiness" and item.repository_id == "repo:one"
    ]
    assert cloud[0].activation_status.value == "unavailable"
    # No findings does not invent healthy/complete for missing heads.
    ai = [
        item
        for item in aggregation.assessment_head_facts
        if item.assessment_head_id == "ai_readiness" and item.repository_id == "repo:one"
    ]
    assert ai[0].coverage_status.value == "unavailable"


def test_finding_recommendation_pa_roadmap_correlation_preserved() -> None:
    _, aggregation, _ = prepare_aggregation()
    assert aggregation.aggregate_counts.finding_count == 2
    assert aggregation.aggregate_counts.recommendation_count == 2
    assert aggregation.aggregate_counts.priority_action_count == 2
    assert aggregation.aggregate_counts.roadmap_initiative_count == 2
    assert aggregation.aggregate_counts.correlation_count == 2
    finding = aggregation.finding_facts[0]
    assert finding.rule_id == "rule.demo"
    assert finding.primary_evidence_id
    assert "snippet" not in finding.limitations
    assert all(item.phase is None or isinstance(item.phase, str) for item in aggregation.roadmap_facts)


def test_coverage_confidence_not_recomputed() -> None:
    _, aggregation, _ = prepare_aggregation()
    coverage = {
        (item.repository_id, item.assessment_head_id, item.coverage_status)
        for item in aggregation.coverage_facts
    }
    assert ("repo:one", "security_intelligence", "complete") in coverage
    assert ("repo:one", "dependency_intelligence", "disabled") in coverage
    confidence = {
        (item.repository_id, item.assessment_head_id, item.confidence_level)
        for item in aggregation.confidence_facts
    }
    assert ("repo:one", "security_intelligence", "high") in confidence


def test_legacy_exclude_policy() -> None:
    policy = IntelligenceAggregationPolicy(legacy_assessment_policy=LegacyAssessmentPolicy.EXCLUDE)
    _, aggregation, _ = prepare_aggregation(
        repos=[
            ("repo:complete", "assessment:complete", "run:c", full_engine_report()),
            ("repo:legacy", "assessment:legacy", "run:l", legacy_flat_report()),
        ],
        policy=policy,
    )
    assert aggregation.aggregate_counts.repository_count == 1
    assert aggregation.repository_index[0].repository_id == "repo:complete"
    assert any("legacy_excluded" in item for item in aggregation.limitations)


def test_legacy_limited_policy_marks_facts() -> None:
    policy = IntelligenceAggregationPolicy(legacy_assessment_policy=LegacyAssessmentPolicy.LIMITED)
    _, aggregation, _ = prepare_aggregation(
        repos=[("repo:legacy", "assessment:legacy", "run:l", legacy_flat_report())],
        policy=policy,
    )
    assert aggregation.aggregate_counts.repository_count == 1
    assert aggregation.repository_index[0].legacy_or_incomplete is True
    # Missing Priority Actions are not fabricated as zero-capable canonical completeness.
    assert aggregation.aggregate_counts.priority_action_count == 0


def test_public_oss_visibility_rejects_private() -> None:
    policy = IntelligenceAggregationPolicy(
        visibility_policy=VisibilityAggregationScope.PUBLIC_OSS
    )
    with pytest.raises(AggregationVisibilityError):
        prepare_aggregation(
            policy=policy,
            visibility=DataVisibility.CUSTOMER_PRIVATE,
            source_type=SourceType.CUSTOMER_PRIVATE,
        )


def test_public_oss_visibility_accepts_public() -> None:
    policy = IntelligenceAggregationPolicy(
        visibility_policy=VisibilityAggregationScope.PUBLIC_OSS
    )
    _, aggregation, _ = prepare_aggregation(
        policy=policy,
        visibility=DataVisibility.PUBLIC,
        source_type=SourceType.PUBLIC_OSS,
    )
    assert aggregation.aggregate_counts.repository_count == 2


def test_unresolved_recommendation_support_fails() -> None:
    broken = full_engine_report()
    broken["assessment"]["deterministic_recommendations"][0]["supporting_finding_ids"] = [
        "finding:missing"
    ]
    source = InMemoryAssessmentReportSource()
    ref = "artifact:assessment:broken:report_json"
    source.put(ref, broken)
    inputs = [
        AssessmentDatasetInput(
            repository_id="repo:broken",
            assessment_id="assessment:broken",
            assessment_run_id="run:broken",
            report_document=deepcopy(broken),
            report_reference=ref,
            pinned_revision="abc123def",
            visibility=DataVisibility.ANONYMIZED,
            source_type=SourceType.PUBLIC_OSS,
        )
    ]
    # Traceability should reject during ingestion.
    result = ingest_assessment_dataset(inputs)
    assert len(result.rejected) == 1


def test_conflicting_technology_versions() -> None:
    report = full_engine_report(
        extra_assessment={
            "technologies": [
                {"name": "Python", "category": "language", "version": "3.11"},
                {"name": "Python", "category": "language", "version": "3.12"},
            ]
        }
    )
    _, aggregation, _ = prepare_aggregation(
        repos=[("repo:one", "assessment:one", "run:one", report)]
    )
    assert any(item.version_state is VersionState.CONFLICTING for item in aggregation.technology_facts)


def test_report_root_population_only() -> None:
    result, aggregation, _ = prepare_aggregation()
    report = EngineeringIntelligenceReport.create(
        title="Aggregation shell",
        report_scope=ReportScope.INTERNAL_VALIDATION_DATASET,
        dataset=result.dataset,
        repository_population=aggregation.repository_population,
    )
    assert report.technology_distribution.observations == ()
    assert report.capability_comparisons == ()
    assert report.recurring_patterns == ()
    assert report.modernization_observations == ()
    assert report.repository_drilldowns == ()


def test_diagnostics_reconcile() -> None:
    _, aggregation, _ = prepare_aggregation()
    diag = aggregation.diagnostics
    assert diag.included_repository_count == aggregation.aggregate_counts.repository_count
    assert diag.finding_fact_count == aggregation.aggregate_counts.finding_count
    assert diag.unresolved_reference_count == 0


def test_no_full_report_embedded() -> None:
    _, aggregation, _ = prepare_aggregation()
    blob = repr(aggregation)
    assert "redacted_excerpt" not in blob
    assert "source_body" not in blob
    assert "/Users/" not in blob
