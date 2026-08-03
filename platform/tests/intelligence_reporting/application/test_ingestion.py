"""Canonical assessment dataset ingestion tests."""

from __future__ import annotations

import copy

import pytest

from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentDatasetInput,
    FailedAssessmentBehavior,
    IntelligenceDatasetSelectionPolicy,
)
from codestrata_platform.intelligence_reporting.application.errors import (
    AmbiguousRepositoryAssessmentError,
    AssessmentTraceabilityError,
    DuplicateAssessmentConflictError,
    MalformedAssessmentReportError,
    UnsafeAssessmentMetadataError,
    UnsupportedAssessmentSchemaError,
)
from codestrata_platform.intelligence_reporting.application.ingestion import (
    ingest_assessment_dataset,
)
from codestrata_platform.intelligence_reporting.application.normalization import (
    stable_canonical_report_digest,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ComparabilityStatus,
    DataVisibility,
    InclusionStatus,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from codestrata_platform.intelligence_reporting.domain.serialization import (
    to_stable_dict,
)
from codestrata_platform.intelligence_reporting.domain.enums import ReportScope
from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)
from tests.intelligence_reporting.application.conftest import (
    full_engine_report,
    legacy_flat_report,
    make_input,
)


def test_valid_report_input_builds_dataset() -> None:
    result = ingest_assessment_dataset(
        [
            make_input(repository_id="repo:one", assessment_id="assessment:one", assessment_run_id="run:one"),
            make_input(
                repository_id="repo:two",
                assessment_id="assessment:two",
                assessment_run_id="run:two",
                report=full_engine_report(
                    finding_id="finding:2",
                    evidence_id="ev:beta",
                    recommendation_id="rec:2",
                    action_id="pa:2",
                    initiative_id="init:2",
                ),
            ),
        ]
    )
    assert result.dataset is not None
    assert result.dataset.repository_count == 2
    assert len(result.included) == 2
    assert result.dataset.dataset_id.value.startswith("dataset:")
    # Full report not embedded — only references/digests on the dataset.
    payload = to_stable_dict(result.dataset)
    assert "findings" not in payload
    assert "priority_actions" not in payload
    assert "deterministic_recommendations" not in payload
    assert "snippet" not in payload
    assert "source_body" not in payload
    assert all(
        item.canonical_report_reference for item in result.dataset.repository_assessments
    )
    assert all(
        snap.canonical_report_digest for snap in result.included
    )


def test_missing_repository_identity_rejected() -> None:
    result = ingest_assessment_dataset(
        [
            AssessmentDatasetInput(
                repository_id="",
                assessment_id="assessment:one",
                assessment_run_id="run:one",
                report_document=full_engine_report(),
            )
        ]
    )
    assert result.dataset is not None
    assert len(result.rejected) == 1
    assert result.rejected[0].exclusion_reason == "incomplete_identity"


def test_unsupported_schema_rejected() -> None:
    report = full_engine_report()
    report["schema_version"] = "2.0"
    result = ingest_assessment_dataset([make_input(report=report)])
    assert len(result.rejected) == 1
    assert result.rejected[0].exclusion_reason == "unsupported_schema"


def test_malformed_report_rejected() -> None:
    result = ingest_assessment_dataset(
        [
            AssessmentDatasetInput(
                repository_id="repo:one",
                assessment_id="assessment:one",
                assessment_run_id="run:one",
                report_document=None,
            )
        ]
    )
    assert len(result.rejected) == 1


def test_traceability_failure_rejected() -> None:
    report = full_engine_report()
    report["assessment"]["priority_actions"][0]["supporting_recommendation_ids"] = [
        "rec:missing"
    ]
    result = ingest_assessment_dataset([make_input(report=report)])
    assert len(result.rejected) == 1
    assert result.rejected[0].exclusion_reason == "traceability_failure"


def test_canonical_ids_preserved_no_regeneration() -> None:
    result = ingest_assessment_dataset([make_input()])
    snap = result.included[0]
    assert [item.entity_id for item in snap.evidence_refs] == ["ev:alpha"]
    assert [item.entity_id for item in snap.finding_refs] == ["finding:1"]
    assert [item.entity_id for item in snap.recommendation_refs] == ["rec:1"]
    assert [item.entity_id for item in snap.priority_action_refs] == ["pa:1"]
    assert [item.entity_id for item in snap.roadmap_refs] == ["init:1"]
    assert [item.entity_id for item in snap.correlation_refs] == ["corr:1"]
    # No snippets copied.
    assert all("excerpt" not in item.metadata for item in snap.evidence_refs)


def test_digest_stable_and_order_invariant() -> None:
    left = full_engine_report()
    right = copy.deepcopy(left)
    # Key order change in Python 3.7+ dict literal rebuild:
    right = {
        "assessment": right["assessment"],
        "schema_version": right["schema_version"],
    }
    assert stable_canonical_report_digest(left) == stable_canonical_report_digest(right)
    mutated = copy.deepcopy(left)
    mutated["assessment"]["findings"][0]["title"] = "Changed"
    assert stable_canonical_report_digest(left) != stable_canonical_report_digest(mutated)


def test_exact_duplicate_deduped() -> None:
    report = full_engine_report()
    result = ingest_assessment_dataset(
        [
            make_input(report=report),
            make_input(report=copy.deepcopy(report)),
        ]
    )
    assert len(result.included) == 1
    assert any(item.code == "exact_duplicate_deduped" for item in result.diagnostics)


def test_conflicting_digest_fails_closed() -> None:
    a = full_engine_report()
    b = full_engine_report()
    b["assessment"]["findings"][0]["title"] = "Different"
    with pytest.raises(DuplicateAssessmentConflictError):
        ingest_assessment_dataset(
            [
                make_input(report=a),
                make_input(report=b),
            ]
        )


def test_same_repository_different_runs_requires_selection() -> None:
    result = ingest_assessment_dataset(
        [
            make_input(assessment_run_id="run:one"),
            make_input(
                assessment_id="assessment:alt",
                assessment_run_id="run:two",
                report=full_engine_report(
                    finding_id="finding:2",
                    evidence_id="ev:beta",
                    recommendation_id="rec:2",
                    action_id="pa:2",
                    initiative_id="init:2",
                ),
            ),
        ]
    )
    assert result.dataset is not None
    assert result.dataset.repository_count == 0
    assert len(result.rejected) == 2
    assert all(
        item.exclusion_reason == "ambiguous_run_selection" for item in result.rejected
    )


def test_explicit_selected_run_succeeds() -> None:
    policy = IntelligenceDatasetSelectionPolicy(
        selected_assessment_runs={"repo:one": "run:two"}
    )
    result = ingest_assessment_dataset(
        [
            make_input(assessment_run_id="run:one"),
            make_input(
                assessment_id="assessment:alt",
                assessment_run_id="run:two",
                report=full_engine_report(
                    finding_id="finding:2",
                    evidence_id="ev:beta",
                    recommendation_id="rec:2",
                    action_id="pa:2",
                    initiative_id="init:2",
                ),
            ),
        ],
        policy=policy,
    )
    assert result.dataset is not None
    assert result.dataset.repository_count == 1
    assert result.included[0].assessment_run_id == "run:two"
    assert any(item.exclusion_reason == "superseded_assessment" for item in result.excluded)


def test_input_ordering_invariant() -> None:
    a = make_input(repository_id="repo:a", assessment_id="assessment:a", assessment_run_id="run:a")
    b = make_input(
        repository_id="repo:b",
        assessment_id="assessment:b",
        assessment_run_id="run:b",
        report=full_engine_report(
            finding_id="finding:b",
            evidence_id="ev:b",
            recommendation_id="rec:b",
            action_id="pa:b",
            initiative_id="init:b",
        ),
    )
    left = ingest_assessment_dataset([a, b])
    right = ingest_assessment_dataset([b, a])
    assert left.dataset is not None and right.dataset is not None
    assert left.dataset.dataset_id.value == right.dataset.dataset_id.value
    assert to_stable_dict(left.dataset) == to_stable_dict(right.dataset)


def test_policy_version_changes_dataset_id() -> None:
    base = ingest_assessment_dataset([make_input()])
    other = ingest_assessment_dataset(
        [make_input()],
        policy=IntelligenceDatasetSelectionPolicy(policy_version="v2"),
    )
    assert base.dataset is not None and other.dataset is not None
    assert base.dataset.dataset_id.value != other.dataset.dataset_id.value


def test_changed_run_changes_dataset_id() -> None:
    left = ingest_assessment_dataset([make_input(assessment_run_id="run:one")])
    right = ingest_assessment_dataset([make_input(assessment_run_id="run:two")])
    assert left.dataset is not None and right.dataset is not None
    assert left.dataset.dataset_id.value != right.dataset.dataset_id.value


def test_assessment_heads_preserved_honestly() -> None:
    snap = ingest_assessment_dataset([make_input()]).included[0]
    assert "security_intelligence" in snap.enabled_assessment_heads
    assert "dependency_intelligence" in snap.disabled_assessment_heads
    assert "cloud_readiness" in snap.unavailable_assessment_heads
    assert "ai_readiness" in snap.missing_assessment_heads
    assert snap.assessment_coverage["security_intelligence"]
    assert snap.assessment_head_confidence["security_intelligence"]
    # No zero-finding inference — empty findings would not invent complete heads.


def test_comparability_complete_and_legacy() -> None:
    complete = make_input(repository_id="repo:complete")
    legacy = make_input(
        repository_id="repo:legacy",
        assessment_id="assessment:legacy",
        assessment_run_id="run:legacy",
        report=legacy_flat_report(),
    )
    result = ingest_assessment_dataset([complete, legacy])
    assert result.comparability is not None
    assert result.comparability.status is ComparabilityStatus.PARTIALLY_COMPARABLE
    assert "repo:complete" in result.comparability.compatible_repository_ids


def test_visibility_and_website_eligibility() -> None:
    private = make_input(
        visibility=DataVisibility.CUSTOMER_PRIVATE,
        source_type=SourceType.CUSTOMER_PRIVATE,
        source_reference="opaque:internal:billing",
        display_name="Acme Billing",
    )
    public = make_input(
        repository_id="repo:public",
        assessment_id="assessment:public",
        assessment_run_id="run:public",
        visibility=DataVisibility.PUBLIC,
        source_type=SourceType.PUBLIC_OSS,
        source_reference="https://github.com/example/public",
        publication_permitted=True,
        display_name="Public Repo",
        report=full_engine_report(
            finding_id="finding:p",
            evidence_id="ev:p",
            recommendation_id="rec:p",
            action_id="pa:p",
            initiative_id="init:p",
        ),
    )
    result = ingest_assessment_dataset([private, public])
    priv = next(item for item in result.included if item.repository_id == "repo:one")
    pub = next(item for item in result.included if item.repository_id == "repo:public")
    assert priv.website_export_eligibility is not None
    assert priv.website_export_eligibility.eligible is False
    assert "private_repository_identity" in priv.website_export_eligibility.blocking_reasons
    assert pub.website_export_eligibility is not None
    assert pub.website_export_eligibility.eligible is True


def test_missing_publication_permission_blocks_eligibility() -> None:
    result = ingest_assessment_dataset(
        [
            make_input(
                visibility=DataVisibility.PUBLIC,
                source_reference="https://github.com/example/x",
                publication_permitted=False,
            )
        ]
    )
    eligibility = result.included[0].website_export_eligibility
    assert eligibility is not None
    assert eligibility.eligible is False
    assert "missing_publication_permission" in eligibility.blocking_reasons


def test_absolute_path_rejected() -> None:
    report = full_engine_report()
    report["assessment"]["findings"][0]["title"] = "/Users/secret/file.py"
    result = ingest_assessment_dataset([make_input(report=report)])
    assert len(result.rejected) == 1
    assert result.rejected[0].exclusion_reason in {
        "unsafe_metadata",
        "unsafe_customer_field",
    } or "unsafe" in (result.rejected[0].exclusion_reason or "")


def test_file_uri_source_reference_rejected() -> None:
    result = ingest_assessment_dataset(
        [
            make_input(source_reference="file:///tmp/repo"),
        ]
    )
    assert len(result.rejected) == 1


def test_fail_fast_policy() -> None:
    policy = IntelligenceDatasetSelectionPolicy(
        failed_assessment_behavior=FailedAssessmentBehavior.FAIL_FAST
    )
    with pytest.raises(
        (UnsupportedAssessmentSchemaError, MalformedAssessmentReportError, UnsafeAssessmentMetadataError)
    ):
        ingest_assessment_dataset(
            [
                make_input(
                    report={**full_engine_report(), "schema_version": "2.0"},
                )
            ],
            policy=policy,
        )


def test_in_memory_report_source() -> None:
    source = InMemoryAssessmentReportSource()
    source.put("artifact:assessment:one:report_json", full_engine_report())
    result = ingest_assessment_dataset(
        [
            AssessmentDatasetInput(
                repository_id="repo:one",
                assessment_id="assessment:one",
                assessment_run_id="run:one",
                report_reference="artifact:assessment:one:report_json",
                pinned_revision="abc123def",
                visibility=DataVisibility.ANONYMIZED,
                source_type=SourceType.IMPORTED_ARTIFACT,
            )
        ],
        report_source=source,
    )
    assert len(result.included) == 1


def test_empty_report_shell_allowed_for_integration() -> None:
    result = ingest_assessment_dataset(
        [
            make_input(repository_id="repo:one"),
            make_input(
                repository_id="repo:two",
                assessment_id="assessment:two",
                assessment_run_id="run:two",
                report=full_engine_report(
                    finding_id="finding:2",
                    evidence_id="ev:2",
                    recommendation_id="rec:2",
                    action_id="pa:2",
                    initiative_id="init:2",
                ),
            ),
        ]
    )
    assert result.dataset is not None
    report = EngineeringIntelligenceReport.create(
        title="Shell report",
        report_scope=ReportScope.INTERNAL_VALIDATION_DATASET,
        dataset=result.dataset,
    )
    assert report.technology_distribution.observations == ()
    assert report.recurring_patterns == ()
    assert report.modernization_observations == ()
    assert report.capability_comparisons == ()


def test_legacy_included_with_limitations() -> None:
    result = ingest_assessment_dataset(
        [make_input(report=legacy_flat_report(), repository_id="repo:legacy")]
    )
    assert len(result.included) == 1
    assert "included_with_legacy_limitations" in result.included[0].limitations
