"""Ports for artifact metadata persistence and content storage."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.artifact.aggregate import AssessmentArtifact
from codestrata_platform.domain.artifact.enums import ArtifactType
from codestrata_platform.domain.artifact.ids import AssessmentArtifactId
from codestrata_platform.domain.artifact.value_objects import ArtifactChecksum, ArtifactReference
from codestrata_platform.domain.assessment.ids import AssessmentId


class ArtifactRepository(Protocol):
    def get(self, artifact_id: AssessmentArtifactId) -> AssessmentArtifact | None: ...

    def save(self, artifact: AssessmentArtifact) -> None: ...

    def list_by_assessment(self, assessment_id: AssessmentId) -> tuple[AssessmentArtifact, ...]: ...

    def find_by_assessment_type_checksum(
        self,
        *,
        assessment_id: AssessmentId,
        artifact_type: ArtifactType,
        checksum: ArtifactChecksum,
    ) -> AssessmentArtifact | None: ...

    def latest_version_for_type(
        self,
        *,
        assessment_id: AssessmentId,
        artifact_type: ArtifactType,
    ) -> int: ...


class ArtifactStorage(Protocol):
    def put(self, *, key: str, content: bytes, content_type: str) -> ArtifactReference: ...

    def get(self, reference: ArtifactReference) -> bytes: ...

    def exists(self, reference: ArtifactReference) -> bool: ...

    def delete(self, reference: ArtifactReference) -> None: ...
