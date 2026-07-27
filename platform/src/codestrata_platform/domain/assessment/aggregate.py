"""Assessment aggregate root.

Records a completed (or in-flight) Community Engine run owned by the Platform.
Does not contain findings, graphs, or RAG state.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.assessment.enums import AssessmentStatus
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.assessment.value_objects import (
    AssessmentMetadata,
    AssessmentReference,
    AssessmentVersion,
    GeneratedReport,
)
from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvalidValueError,
)
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.shared.version import PlatformVersion
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(slots=True)
class Assessment:
    assessment_id: AssessmentId
    repository_id: RepositoryId
    workspace_id: WorkspaceId
    engine_version: PlatformVersion
    assessment_version: AssessmentVersion
    status: AssessmentStatus
    started_at: datetime | None
    completed_at: datetime | None
    generated_reports: tuple[GeneratedReport, ...]
    references: tuple[AssessmentReference, ...]
    metadata: AssessmentMetadata
    audit: AuditInfo
    failure_reason: str | None = None
    _version: int = field(default=0, repr=False)

    @classmethod
    def create(
        cls,
        *,
        repository_id: RepositoryId,
        workspace_id: WorkspaceId,
        engine_version: PlatformVersion | str,
        assessment_version: AssessmentVersion | str,
        assessment_id: AssessmentId | None = None,
        metadata: AssessmentMetadata | None = None,
        audit: AuditInfo | None = None,
    ) -> Assessment:
        return cls(
            assessment_id=assessment_id or AssessmentId.generate(),
            repository_id=repository_id,
            workspace_id=workspace_id,
            engine_version=(
                engine_version
                if isinstance(engine_version, PlatformVersion)
                else PlatformVersion(engine_version)
            ),
            assessment_version=(
                assessment_version
                if isinstance(assessment_version, AssessmentVersion)
                else AssessmentVersion(assessment_version)
            ),
            status=AssessmentStatus.PENDING,
            started_at=None,
            completed_at=None,
            generated_reports=(),
            references=(),
            metadata=metadata or AssessmentMetadata.empty(),
            audit=audit or AuditInfo.create(),
        )

    def start(self, *, at: datetime | None = None) -> None:
        if self.status is not AssessmentStatus.PENDING:
            raise InvalidStateTransitionError(
                f"Cannot start assessment from status {self.status.value}",
                reason_code="assessment_invalid_start",
            )
        moment = at or datetime.now(UTC)
        if moment.tzinfo is None:
            raise InvalidValueError(
                "Assessment timestamps must be timezone-aware",
                reason_code="naive_timestamp",
            )
        self.status = AssessmentStatus.RUNNING
        self.started_at = moment.astimezone(UTC)
        self._touch()

    def complete(
        self,
        *,
        generated_reports: tuple[GeneratedReport, ...] = (),
        references: tuple[AssessmentReference, ...] = (),
        at: datetime | None = None,
    ) -> None:
        if self.status is not AssessmentStatus.RUNNING:
            raise InvalidStateTransitionError(
                f"Cannot complete assessment from status {self.status.value}",
                reason_code="assessment_invalid_complete",
            )
        moment = at or datetime.now(UTC)
        if moment.tzinfo is None:
            raise InvalidValueError(
                "Assessment timestamps must be timezone-aware",
                reason_code="naive_timestamp",
            )
        if self.started_at is not None and moment.astimezone(UTC) < self.started_at:
            raise InvalidValueError(
                "Assessment completion cannot precede start",
                reason_code="assessment_completion_before_start",
            )
        self.status = AssessmentStatus.SUCCEEDED
        self.completed_at = moment.astimezone(UTC)
        self.generated_reports = tuple(generated_reports)
        self.references = tuple(references)
        self.failure_reason = None
        self._touch()

    def fail(self, *, reason: str, at: datetime | None = None) -> None:
        if self.status not in {AssessmentStatus.PENDING, AssessmentStatus.RUNNING}:
            raise InvalidStateTransitionError(
                f"Cannot fail assessment from status {self.status.value}",
                reason_code="assessment_invalid_fail",
            )
        compact = reason.strip()
        if not compact:
            raise InvalidValueError(
                "Assessment failure reason must be non-blank",
                reason_code="empty_failure_reason",
            )
        moment = at or datetime.now(UTC)
        if moment.tzinfo is None:
            raise InvalidValueError(
                "Assessment timestamps must be timezone-aware",
                reason_code="naive_timestamp",
            )
        if self.status is AssessmentStatus.PENDING:
            self.started_at = moment.astimezone(UTC)
        self.status = AssessmentStatus.FAILED
        self.completed_at = moment.astimezone(UTC)
        self.failure_reason = compact
        self._touch()

    def _touch(self) -> None:
        self.audit = self.audit.touch()
        self._version += 1

    def snapshot(self) -> Assessment:
        return replace(
            self,
            generated_reports=self.generated_reports,
            references=self.references,
            metadata=self.metadata,
            audit=self.audit,
        )
