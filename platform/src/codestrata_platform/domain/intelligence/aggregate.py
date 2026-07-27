"""AssessmentIntelligence aggregate root."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvalidValueError,
    InvariantViolationError,
)
from codestrata_platform.domain.intelligence.enums import IntelligenceIngestionStatus
from codestrata_platform.domain.intelligence.ids import AssessmentIntelligenceId
from codestrata_platform.domain.intelligence.value_objects import (
    Finding,
    IntelligenceSchemaVersion,
    Metric,
    Recommendation,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(slots=True)
class AssessmentIntelligence:
    """Normalized assessment intelligence derived from completed artifacts."""

    intelligence_id: AssessmentIntelligenceId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    assessment_id: AssessmentId
    engine_assessment_id: str
    schema_version: IntelligenceSchemaVersion
    parser_version: str
    revision: int
    idempotency_key: str
    status: IntelligenceIngestionStatus
    source_artifact_ids: tuple[str, ...]
    findings: tuple[Finding, ...]
    metrics: tuple[Metric, ...]
    recommendations: tuple[Recommendation, ...]
    audit: AuditInfo
    failure_reason: str | None = None
    diagnostics: tuple[str, ...] = ()
    completed_at: datetime | None = None
    _version: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        self.engine_assessment_id = self.engine_assessment_id.strip()
        if not self.engine_assessment_id:
            raise InvalidValueError(
                "engine_assessment_id must be non-blank",
                reason_code="empty_engine_assessment_id",
            )
        self.parser_version = self.parser_version.strip()
        if not self.parser_version:
            raise InvalidValueError(
                "parser_version must be non-blank",
                reason_code="empty_parser_version",
            )
        compact_key = self.idempotency_key.strip()
        if not compact_key:
            raise InvalidValueError(
                "idempotency_key must be non-blank",
                reason_code="empty_idempotency_key",
            )
        object.__setattr__(self, "idempotency_key", compact_key)
        if self.revision < 1:
            raise InvalidValueError(
                "revision must be >= 1",
                reason_code="invalid_revision",
            )
        self._validate_unique_ids()

    @classmethod
    def create_pending(
        cls,
        *,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        repository_id: RepositoryId,
        assessment_id: AssessmentId,
        engine_assessment_id: str,
        schema_version: IntelligenceSchemaVersion | str,
        parser_version: str,
        revision: int,
        idempotency_key: str,
        source_artifact_ids: tuple[str, ...] | list[str],
        intelligence_id: AssessmentIntelligenceId | None = None,
        audit: AuditInfo | None = None,
    ) -> AssessmentIntelligence:
        if not source_artifact_ids:
            raise InvalidValueError(
                "source_artifact_ids must be non-empty",
                reason_code="empty_source_artifacts",
            )
        normalized_sources = tuple(
            sorted(
                {
                    artifact_id.strip()
                    for artifact_id in source_artifact_ids
                    if artifact_id.strip()
                }
            )
        )
        if not normalized_sources:
            raise InvalidValueError(
                "source_artifact_ids must contain non-blank ids",
                reason_code="empty_source_artifacts",
            )
        return cls(
            intelligence_id=intelligence_id or AssessmentIntelligenceId.generate(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            repository_id=repository_id,
            assessment_id=assessment_id,
            engine_assessment_id=engine_assessment_id,
            schema_version=(
                schema_version
                if isinstance(schema_version, IntelligenceSchemaVersion)
                else IntelligenceSchemaVersion(schema_version)
            ),
            parser_version=parser_version,
            revision=max(1, revision),
            idempotency_key=idempotency_key,
            status=IntelligenceIngestionStatus.PENDING,
            source_artifact_ids=normalized_sources,
            findings=(),
            metrics=(),
            recommendations=(),
            audit=audit or AuditInfo.create(),
        )

    def begin_ingestion(self) -> None:
        if self.status is not IntelligenceIngestionStatus.PENDING:
            raise InvalidStateTransitionError(
                f"Cannot begin ingestion from status {self.status.value}",
                reason_code="intelligence_invalid_begin_ingestion",
            )
        self.status = IntelligenceIngestionStatus.INGESTING
        self._touch()

    def attach_finding(self, finding: Finding) -> None:
        self._require_ingesting()
        if finding.assessment_id != self.assessment_id:
            raise InvariantViolationError(
                "Finding assessment_id must match aggregate assessment_id",
                reason_code="finding_assessment_mismatch",
            )
        if any(existing.finding_id == finding.finding_id for existing in self.findings):
            raise InvariantViolationError(
                f"Duplicate finding_id: {finding.finding_id.value}",
                reason_code="duplicate_finding_id",
            )
        self.findings = (*self.findings, finding)
        self._touch()

    def attach_metric(self, metric: Metric) -> None:
        self._require_ingesting()
        if any(existing.name == metric.name for existing in self.metrics):
            raise InvariantViolationError(
                f"Duplicate metric name: {metric.name.value}",
                reason_code="duplicate_metric_name",
            )
        self.metrics = (*self.metrics, metric)
        self._touch()

    def attach_recommendation(self, recommendation: Recommendation) -> None:
        self._require_ingesting()
        if recommendation.assessment_id != self.assessment_id:
            raise InvariantViolationError(
                "Recommendation assessment_id must match aggregate assessment_id",
                reason_code="recommendation_assessment_mismatch",
            )
        if any(
            existing.recommendation_id == recommendation.recommendation_id
            for existing in self.recommendations
        ):
            raise InvariantViolationError(
                f"Duplicate recommendation_id: {recommendation.recommendation_id.value}",
                reason_code="duplicate_recommendation_id",
            )
        self.recommendations = (*self.recommendations, recommendation)
        self._touch()

    def complete(self, *, at: datetime | None = None) -> None:
        if self.status is IntelligenceIngestionStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Completed intelligence records are immutable",
                reason_code="intelligence_immutable",
            )
        if self.status is not IntelligenceIngestionStatus.INGESTING:
            raise InvalidStateTransitionError(
                f"Cannot complete intelligence from status {self.status.value}",
                reason_code="intelligence_invalid_complete",
            )
        moment = at or datetime.now(UTC)
        if moment.tzinfo is None:
            raise InvalidValueError(
                "Intelligence timestamps must be timezone-aware",
                reason_code="naive_timestamp",
            )
        self.status = IntelligenceIngestionStatus.COMPLETED
        self.completed_at = moment.astimezone(UTC)
        self.failure_reason = None
        self._touch()

    def fail(
        self,
        *,
        reason: str,
        diagnostics: tuple[str, ...] | list[str] = (),
        at: datetime | None = None,
    ) -> None:
        if self.status in {
            IntelligenceIngestionStatus.COMPLETED,
            IntelligenceIngestionStatus.REJECTED,
            IntelligenceIngestionStatus.SUPERSEDED,
        }:
            raise InvalidStateTransitionError(
                f"Cannot fail intelligence from status {self.status.value}",
                reason_code="intelligence_invalid_fail",
            )
        compact = reason.strip()
        if not compact:
            raise InvalidValueError(
                "Failure reason must be non-blank",
                reason_code="empty_failure_reason",
            )
        moment = at or datetime.now(UTC)
        if moment.tzinfo is None:
            raise InvalidValueError(
                "Intelligence timestamps must be timezone-aware",
                reason_code="naive_timestamp",
            )
        self.status = IntelligenceIngestionStatus.FAILED
        self.completed_at = moment.astimezone(UTC)
        self.failure_reason = compact
        self.diagnostics = tuple(item.strip() for item in diagnostics if item.strip())
        self.findings = ()
        self.metrics = ()
        self.recommendations = ()
        self._touch()

    def reject(self, *, reason: str, at: datetime | None = None) -> None:
        if self.status in {
            IntelligenceIngestionStatus.COMPLETED,
            IntelligenceIngestionStatus.SUPERSEDED,
        }:
            raise InvalidStateTransitionError(
                f"Cannot reject intelligence from status {self.status.value}",
                reason_code="intelligence_invalid_reject",
            )
        if self.status is IntelligenceIngestionStatus.REJECTED:
            raise InvalidStateTransitionError(
                "Intelligence is already rejected",
                reason_code="intelligence_already_rejected",
            )
        compact = reason.strip()
        if not compact:
            raise InvalidValueError(
                "Rejection reason must be non-blank",
                reason_code="empty_failure_reason",
            )
        moment = at or datetime.now(UTC)
        if moment.tzinfo is None:
            raise InvalidValueError(
                "Intelligence timestamps must be timezone-aware",
                reason_code="naive_timestamp",
            )
        self.status = IntelligenceIngestionStatus.REJECTED
        self.completed_at = moment.astimezone(UTC)
        self.failure_reason = compact
        self.findings = ()
        self.metrics = ()
        self.recommendations = ()
        self._touch()

    def supersede(self, *, at: datetime | None = None) -> None:
        if self.status is not IntelligenceIngestionStatus.COMPLETED:
            raise InvalidStateTransitionError(
                f"Cannot supersede intelligence from status {self.status.value}",
                reason_code="intelligence_invalid_supersede",
            )
        moment = at or datetime.now(UTC)
        if moment.tzinfo is None:
            raise InvalidValueError(
                "Intelligence timestamps must be timezone-aware",
                reason_code="naive_timestamp",
            )
        self.status = IntelligenceIngestionStatus.SUPERSEDED
        self.completed_at = moment.astimezone(UTC)
        self._touch()

    def _require_ingesting(self) -> None:
        if self.status is IntelligenceIngestionStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Completed intelligence records are immutable",
                reason_code="intelligence_immutable",
            )
        if self.status is not IntelligenceIngestionStatus.INGESTING:
            raise InvalidStateTransitionError(
                f"Cannot attach data from status {self.status.value}",
                reason_code="intelligence_invalid_attach",
            )

    def _validate_unique_ids(self) -> None:
        finding_ids = [item.finding_id for item in self.findings]
        if len(finding_ids) != len(set(finding_ids)):
            raise InvariantViolationError(
                "findings must have unique finding_id values",
                reason_code="duplicate_finding_id",
            )
        recommendation_ids = [item.recommendation_id for item in self.recommendations]
        if len(recommendation_ids) != len(set(recommendation_ids)):
            raise InvariantViolationError(
                "recommendations must have unique recommendation_id values",
                reason_code="duplicate_recommendation_id",
            )

    def _touch(self) -> None:
        self.audit = self.audit.touch()
        self._version += 1

    def snapshot(self) -> AssessmentIntelligence:
        return replace(
            self,
            findings=self.findings,
            metrics=self.metrics,
            recommendations=self.recommendations,
            audit=self.audit,
        )
