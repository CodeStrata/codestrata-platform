"""AssessmentArtifact aggregate root."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.artifact.enums import (
    ArtifactFormat,
    ArtifactStatus,
    ArtifactType,
)
from codestrata_platform.domain.artifact.ids import AssessmentArtifactId
from codestrata_platform.domain.artifact.value_objects import (
    ArtifactChecksum,
    ArtifactMetadata,
    ArtifactReference,
    ArtifactSize,
    ArtifactVersion,
)
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvalidValueError,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.workspace.ids import WorkspaceId

_SUPPORTED_FORMATS: dict[ArtifactType, frozenset[ArtifactFormat]] = {
    ArtifactType.ASSESSMENT_SUMMARY: frozenset({ArtifactFormat.JSON}),
    ArtifactType.REPORT_JSON: frozenset({ArtifactFormat.JSON}),
    ArtifactType.REPORT_HTML: frozenset({ArtifactFormat.HTML}),
    ArtifactType.FINDINGS: frozenset({ArtifactFormat.JSON}),
    ArtifactType.EVIDENCE_MANIFEST: frozenset({ArtifactFormat.JSON, ArtifactFormat.TEXT}),
    ArtifactType.KNOWLEDGE_EXPORT: frozenset({ArtifactFormat.JSON, ArtifactFormat.BINARY}),
}


@dataclass(slots=True)
class AssessmentArtifact:
    """Authorized assessment artifact metadata (content lives in ArtifactStorage)."""

    artifact_id: AssessmentArtifactId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    assessment_id: AssessmentId
    engine_assessment_id: str
    artifact_type: ArtifactType
    format: ArtifactFormat
    schema_version: str
    checksum: ArtifactChecksum
    size: ArtifactSize
    status: ArtifactStatus
    version: ArtifactVersion
    metadata: ArtifactMetadata
    audit: AuditInfo
    storage_reference: ArtifactReference | None = None
    completed_at: datetime | None = None
    failure_reason: str | None = None
    _version: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        self.engine_assessment_id = self.engine_assessment_id.strip()
        if not self.engine_assessment_id:
            raise InvalidValueError(
                "engine_assessment_id must be non-blank",
                reason_code="empty_engine_assessment_id",
            )
        self.schema_version = self.schema_version.strip()
        if not self.schema_version:
            raise InvalidValueError(
                "schema_version must be non-blank",
                reason_code="empty_schema_version",
            )
        allowed = _SUPPORTED_FORMATS.get(self.artifact_type, frozenset())
        if self.format not in allowed:
            raise InvalidValueError(
                f"Format {self.format.value} is not supported for {self.artifact_type.value}",
                reason_code="unsupported_format",
            )

    @classmethod
    def register(
        cls,
        *,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        repository_id: RepositoryId,
        assessment_id: AssessmentId,
        engine_assessment_id: str,
        artifact_type: ArtifactType,
        format: ArtifactFormat,
        schema_version: str,
        checksum: ArtifactChecksum | str,
        size_bytes: int,
        version: int = 1,
        metadata: ArtifactMetadata | None = None,
        artifact_id: AssessmentArtifactId | None = None,
        audit: AuditInfo | None = None,
    ) -> AssessmentArtifact:
        return cls(
            artifact_id=artifact_id or AssessmentArtifactId.generate(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            repository_id=repository_id,
            assessment_id=assessment_id,
            engine_assessment_id=engine_assessment_id,
            artifact_type=artifact_type,
            format=format,
            schema_version=schema_version,
            checksum=(
                checksum if isinstance(checksum, ArtifactChecksum) else ArtifactChecksum(checksum)
            ),
            size=ArtifactSize(size_bytes),
            status=ArtifactStatus.REGISTERED,
            version=ArtifactVersion(version),
            metadata=metadata or ArtifactMetadata.empty(),
            audit=audit or AuditInfo.create(),
        )

    def begin_upload(self) -> None:
        if self.status is not ArtifactStatus.REGISTERED:
            raise InvalidStateTransitionError(
                f"Cannot begin upload from status {self.status.value}",
                reason_code="artifact_invalid_begin_upload",
            )
        self.status = ArtifactStatus.UPLOADING
        self._touch()

    def attach_content(self, *, storage_reference: ArtifactReference | str) -> None:
        """Record stored content while remaining in the uploading lifecycle."""

        if self.status is ArtifactStatus.REGISTERED:
            self.begin_upload()
        if self.status is not ArtifactStatus.UPLOADING:
            raise InvalidStateTransitionError(
                f"Cannot attach content from status {self.status.value}",
                reason_code="artifact_invalid_attach",
            )
        self.storage_reference = (
            storage_reference
            if isinstance(storage_reference, ArtifactReference)
            else ArtifactReference(storage_reference)
        )
        self._touch()

    def complete(
        self,
        *,
        storage_reference: ArtifactReference | str | None = None,
        at: datetime | None = None,
    ) -> None:
        if self.status is ArtifactStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Completed artifacts are immutable",
                reason_code="artifact_immutable",
            )
        if self.status not in {ArtifactStatus.REGISTERED, ArtifactStatus.UPLOADING}:
            raise InvalidStateTransitionError(
                f"Cannot complete artifact from status {self.status.value}",
                reason_code="artifact_invalid_complete",
            )
        ref: ArtifactReference | None
        if storage_reference is None:
            ref = self.storage_reference
        else:
            ref = (
                storage_reference
                if isinstance(storage_reference, ArtifactReference)
                else ArtifactReference(storage_reference)
            )
        if ref is None:
            raise InvalidValueError(
                "Cannot complete artifact without a storage reference",
                reason_code="artifact_missing_content",
            )
        moment = at or datetime.now(UTC)
        if moment.tzinfo is None:
            raise InvalidValueError(
                "Artifact timestamps must be timezone-aware",
                reason_code="naive_timestamp",
            )
        self.storage_reference = ref
        self.status = ArtifactStatus.COMPLETED
        self.completed_at = moment.astimezone(UTC)
        self.failure_reason = None
        self._touch()

    def fail(self, *, reason: str, at: datetime | None = None) -> None:
        if self.status in {ArtifactStatus.COMPLETED, ArtifactStatus.REJECTED}:
            raise InvalidStateTransitionError(
                f"Cannot fail artifact from status {self.status.value}",
                reason_code="artifact_invalid_fail",
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
                "Artifact timestamps must be timezone-aware",
                reason_code="naive_timestamp",
            )
        self.status = ArtifactStatus.FAILED
        self.completed_at = moment.astimezone(UTC)
        self.failure_reason = compact
        self._touch()

    def reject(self, *, reason: str, at: datetime | None = None) -> None:
        if self.status is ArtifactStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Completed artifacts cannot be rejected",
                reason_code="artifact_immutable",
            )
        if self.status is ArtifactStatus.REJECTED:
            raise InvalidStateTransitionError(
                "Artifact is already rejected",
                reason_code="artifact_already_rejected",
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
                "Artifact timestamps must be timezone-aware",
                reason_code="naive_timestamp",
            )
        self.status = ArtifactStatus.REJECTED
        self.completed_at = moment.astimezone(UTC)
        self.failure_reason = compact
        self._touch()

    def _touch(self) -> None:
        self.audit = self.audit.touch()
        self._version += 1

    def snapshot(self) -> AssessmentArtifact:
        return replace(
            self,
            metadata=self.metadata,
            audit=self.audit,
            storage_reference=self.storage_reference,
        )
