"""Identifier stability tests for commercial intelligence reporting."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.domain.dataset import (
    RepositoryAssessmentReference,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    InclusionStatus,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import (
    build_dataset_id,
    build_pattern_id,
    build_report_id,
)
from tests.intelligence_reporting.domain.conftest import make_dataset, make_ref, make_report


def test_dataset_id_stable_under_reordering() -> None:
    a = make_ref(
        repository_id="repo:a",
        assessment_id="assessment:a",
        assessment_run_id="run:a",
    )
    b = make_ref(
        repository_id="repo:b",
        assessment_id="assessment:b",
        assessment_run_id="run:b",
    )
    left = make_dataset((a, b))
    right = make_dataset((b, a))
    assert left.dataset_id.value == right.dataset_id.value
    assert left.dataset_id.value.startswith("dataset:")


def test_changed_assessment_run_changes_dataset_id() -> None:
    base = make_dataset()
    changed = make_dataset(
        (
            make_ref(
                repository_id="repo:one",
                assessment_id="assessment:one",
                assessment_run_id="run:one-changed",
            ),
            make_ref(
                repository_id="repo:two",
                assessment_id="assessment:two",
                assessment_run_id="run:two",
            ),
        )
    )
    assert base.dataset_id.value != changed.dataset_id.value


def test_report_id_stable_and_changes_with_dataset() -> None:
    first = make_report()
    second = make_report()
    assert first.report_id.value == second.report_id.value
    assert first.report_id.value.startswith("eir:")
    other = make_report(
        make_dataset(
            (
                make_ref(
                    repository_id="repo:one",
                    assessment_id="assessment:one",
                    assessment_run_id="run:one",
                ),
                make_ref(
                    repository_id="repo:three",
                    assessment_id="assessment:three",
                    assessment_run_id="run:three",
                ),
            )
        )
    )
    assert other.report_id.value != first.report_id.value


def test_timestamps_do_not_affect_dataset_identity() -> None:
    without_ts = RepositoryAssessmentReference(
        repository_id="repo:a",
        assessment_id="assessment:a",
        assessment_run_id="run:a",
        source_type=SourceType.PUBLIC_OSS,
        assessment_schema_version="1.2",
        inclusion_status=InclusionStatus.INCLUDED,
        visibility=DataVisibility.ANONYMIZED,
        pinned_revision="abc123",
    )
    with_ts = RepositoryAssessmentReference(
        repository_id="repo:a",
        assessment_id="assessment:a",
        assessment_run_id="run:a",
        source_type=SourceType.PUBLIC_OSS,
        assessment_schema_version="1.2",
        inclusion_status=InclusionStatus.INCLUDED,
        visibility=DataVisibility.ANONYMIZED,
        pinned_revision="abc123",
        assessment_timestamp="2099-01-01T00:00:00Z",
    )
    left = build_dataset_id(
        repository_assessment_refs=[without_ts.identity_material()],
        selection_policy_version="intelligence-dataset-selection-v1",
    )
    right = build_dataset_id(
        repository_assessment_refs=[with_ts.identity_material()],
        selection_policy_version="intelligence-dataset-selection-v1",
    )
    assert left.value == right.value


def test_pattern_id_ignores_narrative_alone() -> None:
    left = build_pattern_id(
        pattern_type="recurring_rule",
        normalized_subject="security.credential-literal",
        rule_ids=("security.credential-literal",),
        assessment_head_ids=("security",),
        repository_ids=("repo:one", "repo:two"),
        policy_version="intelligence-pattern-policy-v1",
    )
    right = build_pattern_id(
        pattern_type="recurring_rule",
        normalized_subject="security.credential-literal",
        rule_ids=("security.credential-literal",),
        assessment_head_ids=("security",),
        repository_ids=("repo:two", "repo:one"),
        policy_version="intelligence-pattern-policy-v1",
    )
    assert left.value == right.value


def test_build_report_id_stable() -> None:
    left = build_report_id(
        dataset_id="dataset:abc",
        schema_version="1.0",
        report_scope="internal_validation_dataset",
        assessment_run_identities=("repo:1:run:1",),
        report_policy_version="intelligence-report-policy-v1",
    )
    right = build_report_id(
        dataset_id="dataset:abc",
        schema_version="1.0",
        report_scope="internal_validation_dataset",
        assessment_run_identities=("repo:1:run:1",),
        report_policy_version="intelligence-report-policy-v1",
    )
    assert left.value == right.value


def test_build_report_id_includes_bundle_when_present() -> None:
    without = build_report_id(
        dataset_id="dataset:abc",
        schema_version="1.0",
        report_scope="internal_validation_dataset",
        assessment_run_identities=("repo:1:run:1",),
        report_policy_version="intelligence-report-policy-v1",
    )
    with_bundle = build_report_id(
        dataset_id="dataset:abc",
        schema_version="1.0",
        report_scope="internal_validation_dataset",
        assessment_run_identities=("repo:1:run:1",),
        report_policy_version="intelligence-report-policy-v1",
        interpretation_policy_bundle_id="interp-bundle:abc123",
    )
    assert without.value != with_bundle.value
