"""Domain tests for AssessmentIntelligence aggregate."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvalidValueError,
    InvariantViolationError,
)
from codestrata_platform.domain.intelligence import (
    AssessmentIntelligence,
    EvidenceReference,
    EvidenceReferenceId,
    Finding,
    FindingCategory,
    FindingId,
    FindingSeverity,
    IntelligenceIngestionStatus,
    IntelligenceSchemaVersion,
    Metric,
    MetricName,
    MetricValue,
    MetricValueKind,
    Recommendation,
    RecommendationId,
    RecommendationPriority,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _pending(**overrides: object) -> AssessmentIntelligence:
    params: dict[str, object] = {
        "organization_id": OrganizationId("org:1"),
        "workspace_id": WorkspaceId("workspace:1"),
        "repository_id": RepositoryId("repo:1"),
        "assessment_id": AssessmentId("assessment:1"),
        "engine_assessment_id": "engine-assessment:1",
        "schema_version": IntelligenceSchemaVersion("1.0"),
        "parser_version": "1.0.0",
        "revision": 1,
        "idempotency_key": "abc123",
        "source_artifact_ids": ("artifact:1",),
    }
    params.update(overrides)
    return AssessmentIntelligence.create_pending(**params)  # type: ignore[arg-type]


def _finding(*, finding_id: str = "finding:1") -> Finding:
    return Finding(
        finding_id=FindingId(finding_id),
        assessment_id=AssessmentId("assessment:1"),
        category=FindingCategory.SECURITY,
        rule_id="rule.security.token",
        title="Hard-coded token",
        summary="Detected a hard-coded token in source.",
        severity=FindingSeverity.HIGH,
        confidence=0.9,
        evidence_references=(
            EvidenceReference(
                evidence_id=EvidenceReferenceId.generate(),
                path_reference="src/auth.py",
                line_start=10,
                line_end=12,
            ),
        ),
    )


def _metric() -> Metric:
    return Metric(
        name=MetricName("security.findings.high"),
        value=MetricValue(kind=MetricValueKind.COUNT, value="3"),
    )


def _recommendation(*, recommendation_id: str = "recommendation:1") -> Recommendation:
    return Recommendation(
        recommendation_id=RecommendationId(recommendation_id),
        assessment_id=AssessmentId("assessment:1"),
        category=FindingCategory.SECURITY,
        title="Rotate credentials",
        rationale="Remove hard-coded secrets from source control.",
        priority=RecommendationPriority.HIGH,
        related_finding_ids=("finding:1",),
        dependencies=(),
    )


def test_intelligence_lifecycle_happy_path() -> None:
    record = _pending()
    assert record.status is IntelligenceIngestionStatus.PENDING
    record.begin_ingestion()
    assert record.status is IntelligenceIngestionStatus.INGESTING
    record.attach_finding(_finding())
    record.attach_metric(_metric())
    record.attach_recommendation(_recommendation())
    record.complete()
    assert record.status is IntelligenceIngestionStatus.COMPLETED
    assert record.completed_at is not None
    with pytest.raises(InvalidStateTransitionError):
        record.attach_finding(_finding(finding_id="finding:2"))


def test_intelligence_fail_reject_and_supersede() -> None:
    failed = _pending(idempotency_key="fail")
    failed.begin_ingestion()
    failed.fail(reason="parse error", diagnostics=("invalid_json",))
    assert failed.status is IntelligenceIngestionStatus.FAILED
    assert failed.findings == ()

    rejected = _pending(idempotency_key="reject")
    rejected.reject(reason="policy")
    assert rejected.status is IntelligenceIngestionStatus.REJECTED

    completed = _pending(idempotency_key="done")
    completed.begin_ingestion()
    completed.attach_finding(_finding())
    completed.complete()
    completed.supersede()
    assert completed.status is IntelligenceIngestionStatus.SUPERSEDED


def test_duplicate_ids_and_invalid_metadata() -> None:
    record = _pending()
    record.begin_ingestion()
    record.attach_finding(_finding())
    with pytest.raises(InvariantViolationError):
        record.attach_finding(_finding())
    record.attach_metric(_metric())
    with pytest.raises(InvariantViolationError):
        record.attach_metric(_metric())
    record.attach_metric(
        Metric(
            name=MetricName("security.findings.critical"),
            value=MetricValue(kind=MetricValueKind.COUNT, value="1"),
        )
    )
    record.attach_recommendation(_recommendation())
    with pytest.raises(InvariantViolationError):
        record.attach_recommendation(_recommendation())
    with pytest.raises(InvalidValueError):
        EvidenceReference(
            evidence_id=EvidenceReferenceId.generate(),
            path_reference="/Users/dev/app/.env",
        )
    with pytest.raises(InvariantViolationError):
        record.attach_finding(
            Finding(
                finding_id=FindingId("finding:2"),
                assessment_id=AssessmentId("assessment:2"),
                category=FindingCategory.SECURITY,
                rule_id="rule.security.token",
                title="Mismatch",
                summary="Assessment mismatch.",
                severity=FindingSeverity.LOW,
                confidence=0.5,
                evidence_references=(),
            )
        )
