"""SqlAlchemyAssessmentIntelligenceRepository."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.intelligence.aggregate import AssessmentIntelligence
from codestrata_platform.domain.intelligence.ids import AssessmentIntelligenceId
from codestrata_platform.infrastructure.persistence.mappers.assessment_intelligence_mapper import (
    AssessmentIntelligenceMapper,
)
from codestrata_platform.infrastructure.persistence.models.assessment_intelligence_record import (
    AssessmentIntelligenceRecord,
)
from codestrata_platform.infrastructure.persistence.models.intelligence_source_artifact_record import (
    IntelligenceSourceArtifactRecord,
)


class SqlAlchemyAssessmentIntelligenceRepository:
    """Durable AssessmentIntelligenceRepository adapter."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, intelligence_id: AssessmentIntelligenceId) -> AssessmentIntelligence | None:
        record = self._session.get(AssessmentIntelligenceRecord, intelligence_id.value)
        if record is None:
            return None
        return AssessmentIntelligenceMapper.to_domain(record)

    def save(self, intelligence: AssessmentIntelligence) -> None:
        record = self._session.get(
            AssessmentIntelligenceRecord,
            intelligence.intelligence_id.value,
        )
        if record is None:
            self._session.add(AssessmentIntelligenceMapper.to_record(intelligence))
        else:
            AssessmentIntelligenceMapper.apply_to_record(intelligence, record)

        self._session.execute(
            delete(IntelligenceSourceArtifactRecord).where(
                IntelligenceSourceArtifactRecord.intelligence_id
                == intelligence.intelligence_id.value
            )
        )
        for artifact_id in intelligence.source_artifact_ids:
            self._session.add(
                AssessmentIntelligenceMapper.source_artifact_to_record(
                    intelligence_id=intelligence.intelligence_id.value,
                    assessment_id=intelligence.assessment_id.value,
                    artifact_id=artifact_id,
                )
            )
        self._session.flush()

    def find_by_idempotency_key(
        self,
        *,
        assessment_id: AssessmentId,
        idempotency_key: str,
    ) -> AssessmentIntelligence | None:
        record = self._session.scalars(
            select(AssessmentIntelligenceRecord).where(
                AssessmentIntelligenceRecord.assessment_id == assessment_id.value,
                AssessmentIntelligenceRecord.idempotency_key == idempotency_key.strip(),
            )
        ).first()
        if record is None:
            return None
        return AssessmentIntelligenceMapper.to_domain(record)

    def list_by_assessment(
        self,
        assessment_id: AssessmentId,
    ) -> tuple[AssessmentIntelligence, ...]:
        records = self._session.scalars(
            select(AssessmentIntelligenceRecord)
            .where(AssessmentIntelligenceRecord.assessment_id == assessment_id.value)
            .order_by(AssessmentIntelligenceRecord.revision.asc())
        ).all()
        return tuple(AssessmentIntelligenceMapper.to_domain(record) for record in records)

    def latest_revision_for_assessment(self, assessment_id: AssessmentId) -> int:
        value = self._session.scalar(
            select(func.max(AssessmentIntelligenceRecord.revision)).where(
                AssessmentIntelligenceRecord.assessment_id == assessment_id.value
            )
        )
        return int(value or 0)

    @staticmethod
    def latest_intelligence_id_for_assessment(
        session: Session,
        assessment_id: AssessmentId,
    ) -> str | None:
        return session.scalar(
            select(AssessmentIntelligenceRecord.id)
            .where(AssessmentIntelligenceRecord.assessment_id == assessment_id.value)
            .order_by(AssessmentIntelligenceRecord.revision.desc())
            .limit(1)
        )
