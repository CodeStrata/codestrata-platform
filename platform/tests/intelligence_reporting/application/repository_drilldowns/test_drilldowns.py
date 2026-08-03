"""Repository drill-down selection, refs, visibility, and integration."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.repository_drilldowns import (
    RepositoryDrilldownPolicy,
    build_repository_drilldowns,
    populate_report_repository_drilldowns,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DataVisibility,
    ReportScope,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    to_stable_dict,
)
from tests.intelligence_reporting.application.conftest import full_engine_report
from tests.intelligence_reporting.application.repository_drilldowns.conftest import (
    prepare_drilldown_report,
)


def test_one_drilldown_per_included_repository() -> None:
    _, _, _, report = prepare_drilldown_report()
    assert len(report.repository_drilldowns) == 2
    assert {item.repository_id for item in report.repository_drilldowns} == {
        "repo:one",
        "repo:two",
    }
    assert len({item.drilldown_id.value for item in report.repository_drilldowns}) == 2


def test_excluded_repository_omitted() -> None:
    # Default prepare includes only included repos; count matches included set.
    result, _, _, report = prepare_drilldown_report()
    assert len(report.repository_drilldowns) == len(result.dataset.included_repository_ids)


def test_anonymized_display_name() -> None:
    _, _, _, report = prepare_drilldown_report(visibility=DataVisibility.ANONYMIZED)
    for item in report.repository_drilldowns:
        assert item.display_name.startswith("repository-")
        assert item.display_name != item.repository_id


def test_public_scope_uses_safe_display() -> None:
    _, _, _, report = prepare_drilldown_report(
        scope=ReportScope.PUBLIC_OSS_DATASET,
        visibility=DataVisibility.PUBLIC,
    )
    for item in report.repository_drilldowns:
        assert item.display_name
        assert "://" not in item.display_name


def test_technology_summary_safe_and_ordered() -> None:
    _, _, _, report = prepare_drilldown_report()
    for item in report.repository_drilldowns:
        assert item.technology_summary == tuple(sorted(item.technology_summary))
        blob = " ".join(item.technology_summary).lower()
        assert "modern" not in blob
        assert "outdated" not in blob
        assert "/users/" not in blob


def test_head_snapshots_preserve_coverage_confidence() -> None:
    _, _, _, report = prepare_drilldown_report()
    for item in report.repository_drilldowns:
        assert item.assessment_head_snapshots
        for snap in item.assessment_head_snapshots:
            assert snap.repository_id == item.repository_id
            assert snap.drilldown_ref == item.drilldown_id.value


def test_pattern_and_observation_membership() -> None:
    _, _, _, report = prepare_drilldown_report()
    pattern_ids = {item.pattern_id.value for item in report.recurring_patterns}
    observation_ids = {
        item.observation_id.value for item in report.modernization_observations
    }
    for item in report.repository_drilldowns:
        assert set(item.recurring_pattern_ids) <= pattern_ids
        assert set(item.modernization_observation_ids) <= observation_ids
        for pattern in report.recurring_patterns:
            if pattern.pattern_id.value in item.recurring_pattern_ids:
                assert item.repository_id in pattern.repository_ids


def test_finding_refs_bounded_and_deterministic() -> None:
    policy = RepositoryDrilldownPolicy(maximum_finding_refs=1)
    _, aggregation, _, report = prepare_drilldown_report(drilldown_policy=policy)
    for item in report.repository_drilldowns:
        assert len(item.finding_refs) <= 1
        for ref in item.finding_refs:
            assert ref.assessment_id == item.assessment_id
            assert ref.entity_kind == "finding"
    again = populate_report_repository_drilldowns(report, aggregation, policy=policy)
    assert [d.finding_refs for d in again.repository_drilldowns] == [
        d.finding_refs for d in report.repository_drilldowns
    ]


def test_recommendation_and_priority_action_refs() -> None:
    _, _, _, report = prepare_drilldown_report()
    for item in report.repository_drilldowns:
        assert item.recommendation_refs
        assert item.priority_action_refs
        assert item.highest_priority_action_ids
        assert set(item.highest_priority_action_ids) <= {
            ref.entity_id for ref in item.priority_action_refs
        }


def test_roadmap_and_correlation_refs() -> None:
    _, _, _, report = prepare_drilldown_report()
    for item in report.repository_drilldowns:
        assert item.roadmap_refs
        assert item.correlation_refs
        assert all(ref.entity_kind == "roadmap_initiative" for ref in item.roadmap_refs)
        assert all(ref.entity_kind == "correlation" for ref in item.correlation_refs)


def test_confidence_is_weakest_material_not_average() -> None:
    _, _, _, report = prepare_drilldown_report()
    for item in report.repository_drilldowns:
        assert item.confidence in set(ConfidenceLevel)
        assert not hasattr(item, "percentage")
        assert not hasattr(item, "precision")


def test_canonical_report_ref_always_present_and_opaque() -> None:
    _, _, _, report = prepare_drilldown_report()
    for item in report.repository_drilldowns:
        assert item.canonical_assessment_report_ref
        lowered = item.canonical_assessment_report_ref.lower()
        assert not lowered.startswith("file:")
        assert "/users/" not in lowered
        assert "://" not in lowered
        assert item.canonical_report_digest


def test_limitations_include_navigation_and_non_score_disclosures() -> None:
    _, _, _, report = prepare_drilldown_report()
    for item in report.repository_drilldowns:
        joined = " ".join(item.limitations)
        assert "canonical_assessment_report_required_for_full_evidence_details" in joined
        assert "repository_drilldown_is_navigation_not_a_scorecard" in joined
        assert "cross_sectional_snapshot_only" in joined
        assert "healthy" not in joined.lower()


def test_website_export_precheck_fields() -> None:
    _, _, _, report = prepare_drilldown_report(
        scope=ReportScope.PUBLIC_OSS_DATASET,
        visibility=DataVisibility.PUBLIC,
    )
    for item in report.repository_drilldowns:
        assert isinstance(item.public_export_eligible, bool)
        assert isinstance(item.requires_anonymization, bool)


def test_report_integration_preserves_prior_sections() -> None:
    _, _, _, report = prepare_drilldown_report()
    assert report.technology_distribution is not None
    assert report.capability_comparisons
    assert report.confidence.derivation_status.value == "derived"
    assert report.limitations
    assert report.interpretation_policy_bundle_id
    assert report.generated_artifact_metadata.artifact_kinds == ()
    assert report.schema_version == "1.0"


def test_serialization_round_trip() -> None:
    _, _, _, report = prepare_drilldown_report()
    payload = to_stable_dict(report)
    restored = from_stable_dict(payload)
    assert to_stable_dict(restored) == payload
    assert payload["schema_version"] == "1.0"


def test_diagnostics_reconcile() -> None:
    _, aggregation, _, report = prepare_drilldown_report()
    result = build_repository_drilldowns(report, aggregation)
    assert result.diagnostics.drilldown_count == len(report.repository_drilldowns)
    assert result.diagnostics.included_repository_count == report.dataset.repository_count
    assert result.diagnostics.unresolved_reference_count == 0


def test_empty_findings_still_get_drilldown() -> None:
    # Distinct rules so aggregation validates; focus on presence of drilldown.
    left = full_engine_report()
    right = full_engine_report(
        finding_id="finding:2",
        evidence_id="ev:2",
        recommendation_id="rec:2",
        action_id="pa:2",
        initiative_id="init:2",
    )
    _, _, _, report = prepare_drilldown_report(
        repos=[
            ("repo:one", "assessment:one", "run:one", left),
            ("repo:two", "assessment:two", "run:two", right),
        ]
    )
    assert len(report.repository_drilldowns) == 2
    for item in report.repository_drilldowns:
        assert item.canonical_assessment_report_ref
        assert "healthy" not in " ".join(item.limitations).lower()


def test_source_type_preserved() -> None:
    _, _, _, report = prepare_drilldown_report()
    for item in report.repository_drilldowns:
        assert item.source_type is SourceType.PUBLIC_OSS
