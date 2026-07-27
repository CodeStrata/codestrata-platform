"""Artifact application models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.artifact import (
    ArtifactFormat,
    ArtifactStatus,
    ArtifactType,
    AssessmentArtifact,
    AssessmentArtifactId,
)
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class ArtifactRegistration:
    artifact_id: AssessmentArtifactId
    assessment_id: AssessmentId
    artifact_type: ArtifactType
    checksum: str
    status: ArtifactStatus
    version: int
    created: bool


@dataclass(frozen=True, slots=True)
class ArtifactSummary:
    artifact_id: AssessmentArtifactId
    assessment_id: AssessmentId
    artifact_type: ArtifactType
    format: ArtifactFormat
    checksum: str
    size_bytes: int
    status: ArtifactStatus
    version: int
    schema_version: str


@dataclass(frozen=True, slots=True)
class ArtifactDetails:
    artifact_id: AssessmentArtifactId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    assessment_id: AssessmentId
    engine_assessment_id: str
    artifact_type: ArtifactType
    format: ArtifactFormat
    schema_version: str
    checksum: str
    size_bytes: int
    status: ArtifactStatus
    version: int
    metadata: dict[str, str]
    storage_key: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    failure_reason: str | None

    @classmethod
    def from_aggregate(cls, artifact: AssessmentArtifact) -> ArtifactDetails:
        return cls(
            artifact_id=artifact.artifact_id,
            organization_id=artifact.organization_id,
            workspace_id=artifact.workspace_id,
            repository_id=artifact.repository_id,
            assessment_id=artifact.assessment_id,
            engine_assessment_id=artifact.engine_assessment_id,
            artifact_type=artifact.artifact_type,
            format=artifact.format,
            schema_version=artifact.schema_version,
            checksum=artifact.checksum.value,
            size_bytes=artifact.size.bytes,
            status=artifact.status,
            version=artifact.version.value,
            metadata=dict(artifact.metadata.attributes),
            storage_key=(
                artifact.storage_reference.value if artifact.storage_reference else None
            ),
            created_at=artifact.audit.created_at.value,
            updated_at=artifact.audit.updated_at.value,
            completed_at=artifact.completed_at,
            failure_reason=artifact.failure_reason,
        )

    def to_summary(self) -> ArtifactSummary:
        return ArtifactSummary(
            artifact_id=self.artifact_id,
            assessment_id=self.assessment_id,
            artifact_type=self.artifact_type,
            format=self.format,
            checksum=self.checksum,
            size_bytes=self.size_bytes,
            status=self.status,
            version=self.version,
            schema_version=self.schema_version,
        )


@dataclass(frozen=True, slots=True)
class ArtifactIngestionResult:
    artifact_id: AssessmentArtifactId
    status: ArtifactStatus
    checksum: str
    size_bytes: int
    storage_key: str | None
