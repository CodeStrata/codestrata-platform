"""Report identity includes interpretation-policy bundle."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.report_quality import (
    ReportQualityPolicy,
    populate_report_quality,
)
from codestrata_platform.intelligence_reporting.domain.enums import ReportScope
from codestrata_platform.intelligence_reporting.domain.identifiers import build_report_id
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
    EngineeringIntelligenceReport,
)
from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    to_stable_dict,
)
from tests.intelligence_reporting.application.report_quality.conftest import (
    prepare_quality_report,
)
from tests.intelligence_reporting.domain.conftest import make_report


def test_same_dataset_bundle_stable_report_id() -> None:
    _, aggregation, _, report_a = prepare_quality_report()
    _, _, _, report_b = prepare_quality_report()
    # Distinct dataset ingestions may differ; compare rebuild on same report.
    rebuilt = populate_report_quality(report_a, aggregation)
    assert rebuilt.report_id.value == report_a.report_id.value
    assert rebuilt.interpretation_policy_bundle_id == report_a.interpretation_policy_bundle_id


def test_changed_bundle_changes_report_id() -> None:
    result, aggregation, _, report = prepare_quality_report()
    original_id = report.report_id.value
    # Strip quality, rebuild with altered quality policy.
    base = EngineeringIntelligenceReport.create(
        title=report.title,
        report_scope=report.report_scope,
        dataset=result.dataset,
        technology_distribution=report.technology_distribution,
        capability_comparisons=report.capability_comparisons,
        recurring_patterns=report.recurring_patterns,
        assessment_head_distributions=report.assessment_head_distributions,
        modernization_observations=report.modernization_observations,
    )
    altered = populate_report_quality(
        base,
        aggregation,
        policy=ReportQualityPolicy(small_sample_threshold=10),
    )
    assert altered.interpretation_policy_bundle_id != report.interpretation_policy_bundle_id
    assert altered.report_id.value != original_id


def test_changed_dataset_changes_report_id() -> None:
    _, _, _, report_a = prepare_quality_report()
    from tests.intelligence_reporting.application.conftest import full_engine_report

    _, _, _, report_b = prepare_quality_report(
        repos=[
            ("repo:a", "assessment:a", "run:a", full_engine_report()),
            (
                "repo:b",
                "assessment:b",
                "run:b",
                full_engine_report(
                    finding_id="finding:2",
                    evidence_id="ev:2",
                    recommendation_id="rec:2",
                    action_id="pa:2",
                    initiative_id="init:2",
                ),
            ),
            (
                "repo:c",
                "assessment:c",
                "run:c",
                full_engine_report(
                    finding_id="finding:3",
                    evidence_id="ev:3",
                    recommendation_id="rec:3",
                    action_id="pa:3",
                    initiative_id="init:3",
                ),
            ),
        ]
    )
    assert report_a.dataset.dataset_id.value != report_b.dataset.dataset_id.value
    assert report_a.report_id.value != report_b.report_id.value


def test_build_report_id_ordering_invariant() -> None:
    left = build_report_id(
        dataset_id="dataset:abc",
        schema_version="1.0",
        report_scope="internal_validation_dataset",
        assessment_run_identities=("repo:2:run:2", "repo:1:run:1"),
        report_policy_version="intelligence-report-policy-v1",
        interpretation_policy_bundle_id="interp-bundle:xyz",
    )
    right = build_report_id(
        dataset_id="dataset:abc",
        schema_version="1.0",
        report_scope="internal_validation_dataset",
        assessment_run_identities=("repo:1:run:1", "repo:2:run:2"),
        report_policy_version="intelligence-report-policy-v1",
        interpretation_policy_bundle_id="interp-bundle:xyz",
    )
    assert left.value == right.value


def test_old_payload_without_bundle_loads() -> None:
    report = make_report()
    payload = to_stable_dict(report)
    assert payload.get("interpretation_policy_bundle_id") == ""
    payload.pop("interpretation_policy_bundle_id", None)
    # methodology may include empty bundle fields from new defaults
    methodology = dict(payload.get("methodology") or {})
    methodology.pop("interpretation_policy_bundle_id", None)
    payload["methodology"] = methodology
    restored = from_stable_dict(payload)
    assert restored.interpretation_policy_bundle_id == ""
    assert restored.schema_version == ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION


def test_report_schema_remains_1_0() -> None:
    _, _, _, report = prepare_quality_report(scope=ReportScope.PUBLIC_OSS_DATASET)
    assert report.schema_version == "1.0"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
