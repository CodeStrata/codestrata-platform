"""In-memory AssessmentArtifact repository."""

from __future__ import annotations

from codestrata_platform.domain.artifact import (
    ArtifactChecksum,
    ArtifactType,
    AssessmentArtifact,
    AssessmentArtifactId,
)
from codestrata_platform.domain.assessment.ids import AssessmentId


class InMemoryArtifactRepository:
    def __init__(self) -> None:
        self._items: dict[str, AssessmentArtifact] = {}

    def get(self, artifact_id: AssessmentArtifactId) -> AssessmentArtifact | None:
        item = self._items.get(artifact_id.value)
        return item.snapshot() if item is not None else None

    def save(self, artifact: AssessmentArtifact) -> None:
        self._items[artifact.artifact_id.value] = artifact.snapshot()

    def list_by_assessment(self, assessment_id: AssessmentId) -> tuple[AssessmentArtifact, ...]:
        return tuple(
            item.snapshot()
            for item in self._items.values()
            if item.assessment_id == assessment_id
        )

    def find_by_assessment_type_checksum(
        self,
        *,
        assessment_id: AssessmentId,
        artifact_type: ArtifactType,
        checksum: ArtifactChecksum,
    ) -> AssessmentArtifact | None:
        for item in self._items.values():
            if (
                item.assessment_id == assessment_id
                and item.artifact_type is artifact_type
                and item.checksum == checksum
            ):
                return item.snapshot()
        return None

    def latest_version_for_type(
        self,
        *,
        assessment_id: AssessmentId,
        artifact_type: ArtifactType,
    ) -> int:
        versions = [
            item.version.value
            for item in self._items.values()
            if item.assessment_id == assessment_id and item.artifact_type is artifact_type
        ]
        return max(versions) if versions else 0
