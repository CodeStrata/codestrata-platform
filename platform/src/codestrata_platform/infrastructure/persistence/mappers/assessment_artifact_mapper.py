"""AssessmentArtifact ↔ AssessmentArtifactRecord mapper."""

from __future__ import annotations

from codestrata_platform.domain.artifact import (
    ArtifactChecksum,
    ArtifactFormat,
    ArtifactMetadata,
    ArtifactReference,
    ArtifactSize,
    ArtifactStatus,
    ArtifactType,
    ArtifactVersion,
    AssessmentArtifact,
    AssessmentArtifactId,
)
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import audit_from_record
from codestrata_platform.infrastructure.persistence.models.assessment_artifact_record import (
    AssessmentArtifactRecord,
)


class AssessmentArtifactMapper:
    @staticmethod
    def to_record(artifact: AssessmentArtifact) -> AssessmentArtifactRecord:
        return AssessmentArtifactRecord(
            id=artifact.artifact_id.value,
            organization_id=artifact.organization_id.value,
            workspace_id=artifact.workspace_id.value,
            repository_id=artifact.repository_id.value,
            assessment_id=artifact.assessment_id.value,
            engine_assessment_id=artifact.engine_assessment_id,
            artifact_type=artifact.artifact_type.value,
            format=artifact.format.value,
            schema_version=artifact.schema_version,
            checksum=artifact.checksum.value,
            size_bytes=artifact.size.bytes,
            status=artifact.status.value,
            version=artifact.version.value,
            metadata_json=dict(artifact.metadata.attributes),
            storage_reference=(
                artifact.storage_reference.value if artifact.storage_reference else None
            ),
            created_at=artifact.audit.created_at.value,
            updated_at=artifact.audit.updated_at.value,
            completed_at=artifact.completed_at,
            failure_reason=artifact.failure_reason,
            optimistic_version=artifact._version,
        )

    @staticmethod
    def apply_to_record(artifact: AssessmentArtifact, record: AssessmentArtifactRecord) -> None:
        record.organization_id = artifact.organization_id.value
        record.workspace_id = artifact.workspace_id.value
        record.repository_id = artifact.repository_id.value
        record.assessment_id = artifact.assessment_id.value
        record.engine_assessment_id = artifact.engine_assessment_id
        record.artifact_type = artifact.artifact_type.value
        record.format = artifact.format.value
        record.schema_version = artifact.schema_version
        record.checksum = artifact.checksum.value
        record.size_bytes = artifact.size.bytes
        record.status = artifact.status.value
        record.version = artifact.version.value
        record.metadata_json = dict(artifact.metadata.attributes)
        record.storage_reference = (
            artifact.storage_reference.value if artifact.storage_reference else None
        )
        record.created_at = artifact.audit.created_at.value
        record.updated_at = artifact.audit.updated_at.value
        record.completed_at = artifact.completed_at
        record.failure_reason = artifact.failure_reason
        record.optimistic_version = artifact._version

    @staticmethod
    def to_domain(record: AssessmentArtifactRecord) -> AssessmentArtifact:
        return AssessmentArtifact(
            artifact_id=AssessmentArtifactId(record.id),
            organization_id=OrganizationId(record.organization_id),
            workspace_id=WorkspaceId(record.workspace_id),
            repository_id=RepositoryId(record.repository_id),
            assessment_id=AssessmentId(record.assessment_id),
            engine_assessment_id=record.engine_assessment_id,
            artifact_type=ArtifactType(record.artifact_type),
            format=ArtifactFormat(record.format),
            schema_version=record.schema_version,
            checksum=ArtifactChecksum(record.checksum),
            size=ArtifactSize(record.size_bytes),
            status=ArtifactStatus(record.status),
            version=ArtifactVersion(record.version),
            metadata=ArtifactMetadata(dict(record.metadata_json or {})),
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            storage_reference=(
                ArtifactReference(record.storage_reference)
                if record.storage_reference
                else None
            ),
            completed_at=record.completed_at,
            failure_reason=record.failure_reason,
            _version=record.optimistic_version,
        )
