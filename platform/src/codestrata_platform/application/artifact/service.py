"""DefaultArtifactService — orchestrates artifact registration and storage."""

from __future__ import annotations

import hashlib

from codestrata_platform.application.commands.artifact import (
    CompleteArtifactCommand,
    FailArtifactCommand,
    RegisterArtifactCommand,
    UploadArtifactCommand,
)
from codestrata_platform.application.common.errors import (
    NotFoundError,
    PayloadTooLargeError,
    ValidationError,
)
from codestrata_platform.application.models.artifact import (
    ArtifactDetails,
    ArtifactIngestionResult,
    ArtifactRegistration,
    ArtifactSummary,
)
from codestrata_platform.application.queries.artifact import (
    GetArtifactQuery,
    ListAssessmentArtifactsQuery,
)
from codestrata_platform.domain.artifact import (
    ArtifactChecksum,
    ArtifactMetadata,
    ArtifactRepository,
    ArtifactStatus,
    ArtifactStorage,
    AssessmentArtifact,
    AssessmentArtifactId,
)
from codestrata_platform.domain.assessment import AssessmentRepository
from codestrata_platform.domain.repository import RepositoryRepository


class DefaultArtifactService:
    """Application orchestration for AssessmentArtifact lifecycle."""

    def __init__(
        self,
        *,
        artifacts: ArtifactRepository,
        storage: ArtifactStorage,
        assessments: AssessmentRepository,
        repositories: RepositoryRepository,
        max_artifact_bytes: int = 10_485_760,
    ) -> None:
        self._artifacts = artifacts
        self._storage = storage
        self._assessments = assessments
        self._repositories = repositories
        self._max_artifact_bytes = max_artifact_bytes

    def register_artifact(self, command: RegisterArtifactCommand) -> ArtifactRegistration:
        if command.size_bytes > self._max_artifact_bytes:
            raise PayloadTooLargeError(
                f"Artifact exceeds maximum size of {self._max_artifact_bytes} bytes",
                reason_code="payload_too_large",
            )

        assessment = self._assessments.get(command.assessment_id)
        if assessment is None:
            raise NotFoundError(
                f"Assessment not found: {command.assessment_id.value}",
                reason_code="assessment_not_found",
            )

        repository = self._repositories.get(assessment.repository_id)
        if repository is None:
            raise NotFoundError(
                f"Repository not found: {assessment.repository_id.value}",
                reason_code="repository_not_found",
            )

        checksum = ArtifactChecksum(command.checksum)
        existing = self._artifacts.find_by_assessment_type_checksum(
            assessment_id=command.assessment_id,
            artifact_type=command.artifact_type,
            checksum=checksum,
        )
        if existing is not None:
            return ArtifactRegistration(
                artifact_id=existing.artifact_id,
                assessment_id=existing.assessment_id,
                artifact_type=existing.artifact_type,
                checksum=existing.checksum.value,
                status=existing.status,
                version=existing.version.value,
                created=False,
            )

        next_version = (
            self._artifacts.latest_version_for_type(
                assessment_id=command.assessment_id,
                artifact_type=command.artifact_type,
            )
            + 1
        )
        artifact = AssessmentArtifact.register(
            organization_id=repository.organization_id,
            workspace_id=assessment.workspace_id,
            repository_id=assessment.repository_id,
            assessment_id=assessment.assessment_id,
            engine_assessment_id=command.engine_assessment_id,
            artifact_type=command.artifact_type,
            format=command.format,
            schema_version=command.schema_version,
            checksum=checksum,
            size_bytes=command.size_bytes,
            version=max(1, next_version),
            metadata=(
                ArtifactMetadata(dict(command.metadata))
                if command.metadata is not None
                else None
            ),
        )
        self._artifacts.save(artifact)
        return ArtifactRegistration(
            artifact_id=artifact.artifact_id,
            assessment_id=artifact.assessment_id,
            artifact_type=artifact.artifact_type,
            checksum=artifact.checksum.value,
            status=artifact.status,
            version=artifact.version.value,
            created=True,
        )

    def upload_artifact(self, command: UploadArtifactCommand) -> ArtifactIngestionResult:
        artifact = self._require(command.artifact_id)
        if len(command.content) > self._max_artifact_bytes:
            raise PayloadTooLargeError(
                f"Artifact exceeds maximum size of {self._max_artifact_bytes} bytes",
                reason_code="payload_too_large",
            )
        if len(command.content) != artifact.size.bytes:
            raise ValidationError(
                "Uploaded content length does not match registered size",
                reason_code="content_length_mismatch",
            )
        digest = hashlib.sha256(command.content).hexdigest()
        if digest != ArtifactChecksum(command.declared_checksum).value:
            raise ValidationError(
                "Declared checksum does not match uploaded content",
                reason_code="checksum_mismatch",
            )
        if digest != artifact.checksum.value:
            raise ValidationError(
                "Uploaded content checksum does not match registered checksum",
                reason_code="checksum_mismatch",
            )

        key = (
            f"artifacts/{artifact.assessment_id.value}/"
            f"{artifact.artifact_type.value}/"
            f"v{artifact.version.value}-{artifact.checksum.value}"
        )
        content_type = {
            "json": "application/json",
            "html": "text/html",
            "text": "text/plain",
            "binary": "application/octet-stream",
        }.get(artifact.format.value, "application/octet-stream")

        reference = self._storage.put(key=key, content=command.content, content_type=content_type)
        artifact.attach_content(storage_reference=reference)
        self._artifacts.save(artifact)
        return ArtifactIngestionResult(
            artifact_id=artifact.artifact_id,
            status=artifact.status,
            checksum=artifact.checksum.value,
            size_bytes=artifact.size.bytes,
            storage_key=reference.value,
        )

    def complete_artifact(self, command: CompleteArtifactCommand) -> ArtifactDetails:
        artifact = self._require(command.artifact_id)
        if artifact.status is ArtifactStatus.COMPLETED:
            return ArtifactDetails.from_aggregate(artifact)
        if artifact.storage_reference is None:
            raise ValidationError(
                "Cannot complete artifact without uploaded content",
                reason_code="artifact_missing_content",
            )
        if not self._storage.exists(artifact.storage_reference):
            raise ValidationError(
                "Stored artifact content is missing",
                reason_code="artifact_content_missing",
            )
        artifact.complete()
        self._artifacts.save(artifact)
        return ArtifactDetails.from_aggregate(artifact)


    def fail_artifact(self, command: FailArtifactCommand) -> ArtifactDetails:
        artifact = self._require(command.artifact_id)
        artifact.fail(reason=command.reason)
        self._artifacts.save(artifact)
        return ArtifactDetails.from_aggregate(artifact)

    def get_artifact(self, query: GetArtifactQuery) -> ArtifactDetails:
        return ArtifactDetails.from_aggregate(self._require(query.artifact_id))

    def list_assessment_artifacts(
        self,
        query: ListAssessmentArtifactsQuery,
    ) -> tuple[ArtifactSummary, ...]:
        assessment = self._assessments.get(query.assessment_id)
        if assessment is None:
            raise NotFoundError(
                f"Assessment not found: {query.assessment_id.value}",
                reason_code="assessment_not_found",
            )
        items = self._artifacts.list_by_assessment(query.assessment_id)
        return tuple(ArtifactDetails.from_aggregate(item).to_summary() for item in items)

    def _require(self, artifact_id: AssessmentArtifactId) -> AssessmentArtifact:
        artifact = self._artifacts.get(artifact_id)
        if artifact is None:
            raise NotFoundError(
                f"Artifact not found: {artifact_id.value}",
                reason_code="artifact_not_found",
            )
        return artifact
