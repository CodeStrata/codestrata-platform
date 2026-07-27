"""SqlAlchemyAssessmentArtifactRepository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from codestrata_platform.domain.artifact import (
    ArtifactChecksum,
    ArtifactType,
    AssessmentArtifact,
    AssessmentArtifactId,
)
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.infrastructure.persistence.mappers.assessment_artifact_mapper import (
    AssessmentArtifactMapper,
)
from codestrata_platform.infrastructure.persistence.models.assessment_artifact_record import (
    AssessmentArtifactRecord,
)


class SqlAlchemyAssessmentArtifactRepository:
    """Durable ArtifactRepository adapter (metadata only)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, artifact_id: AssessmentArtifactId) -> AssessmentArtifact | None:
        record = self._session.get(AssessmentArtifactRecord, artifact_id.value)
        if record is None:
            return None
        return AssessmentArtifactMapper.to_domain(record)

    def save(self, artifact: AssessmentArtifact) -> None:
        record = self._session.get(AssessmentArtifactRecord, artifact.artifact_id.value)
        if record is None:
            self._session.add(AssessmentArtifactMapper.to_record(artifact))
        else:
            AssessmentArtifactMapper.apply_to_record(artifact, record)
        self._session.flush()

    def list_by_assessment(self, assessment_id: AssessmentId) -> tuple[AssessmentArtifact, ...]:
        records = self._session.scalars(
            select(AssessmentArtifactRecord)
            .where(AssessmentArtifactRecord.assessment_id == assessment_id.value)
            .order_by(AssessmentArtifactRecord.created_at.asc())
        ).all()
        return tuple(AssessmentArtifactMapper.to_domain(record) for record in records)

    def find_by_assessment_type_checksum(
        self,
        *,
        assessment_id: AssessmentId,
        artifact_type: ArtifactType,
        checksum: ArtifactChecksum,
    ) -> AssessmentArtifact | None:
        record = self._session.scalars(
            select(AssessmentArtifactRecord).where(
                AssessmentArtifactRecord.assessment_id == assessment_id.value,
                AssessmentArtifactRecord.artifact_type == artifact_type.value,
                AssessmentArtifactRecord.checksum == checksum.value,
            )
        ).first()
        if record is None:
            return None
        return AssessmentArtifactMapper.to_domain(record)

    def latest_version_for_type(
        self,
        *,
        assessment_id: AssessmentId,
        artifact_type: ArtifactType,
    ) -> int:
        value = self._session.scalar(
            select(func.max(AssessmentArtifactRecord.version)).where(
                AssessmentArtifactRecord.assessment_id == assessment_id.value,
                AssessmentArtifactRecord.artifact_type == artifact_type.value,
            )
        )
        return int(value or 0)
