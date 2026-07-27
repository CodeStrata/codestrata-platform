"""SqlAlchemyAssessmentRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from codestrata_platform.domain.assessment import Assessment, AssessmentId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers.assessment_mapper import (
    AssessmentMapper,
)
from codestrata_platform.infrastructure.persistence.models.assessment_record import (
    AssessmentRecord,
)


class SqlAlchemyAssessmentRepository:
    """Durable AssessmentRepository adapter."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, assessment_id: AssessmentId) -> Assessment | None:
        record = self._session.get(AssessmentRecord, assessment_id.value)
        if record is None:
            return None
        return AssessmentMapper.to_domain(record)

    def save(self, assessment: Assessment) -> None:
        record = self._session.get(AssessmentRecord, assessment.assessment_id.value)
        if record is None:
            self._session.add(AssessmentMapper.to_record(assessment))
        else:
            AssessmentMapper.apply_to_record(assessment, record)
        self._session.flush()

    def list_by_repository(self, repository_id: RepositoryId) -> tuple[Assessment, ...]:
        records = self._session.scalars(
            select(AssessmentRecord).where(AssessmentRecord.repository_id == repository_id.value)
        ).all()
        return tuple(AssessmentMapper.to_domain(record) for record in records)

    def list_by_workspace(self, workspace_id: WorkspaceId) -> tuple[Assessment, ...]:
        records = self._session.scalars(
            select(AssessmentRecord).where(AssessmentRecord.workspace_id == workspace_id.value)
        ).all()
        return tuple(AssessmentMapper.to_domain(record) for record in records)
