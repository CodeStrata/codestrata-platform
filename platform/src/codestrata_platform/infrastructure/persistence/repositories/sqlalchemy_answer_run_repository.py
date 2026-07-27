"""SqlAlchemy answer run repository."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from codestrata_platform.domain.answering.answer import EngineeringAnswerRun
from codestrata_platform.domain.answering.identifiers import AnswerRunId
from codestrata_platform.domain.answering.lifecycle import AnswerStatus
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.infrastructure.persistence.mappers.answer_mapper import AnswerRunMapper
from codestrata_platform.infrastructure.persistence.models.answer_records import (
    EngineeringAnswerCitationRecord,
    EngineeringAnswerRunRecord,
)


class SqlAlchemyAnswerRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, answer_run_id: AnswerRunId) -> EngineeringAnswerRun | None:
        record = self._session.get(EngineeringAnswerRunRecord, answer_run_id.value)
        if record is None:
            return None
        return self._to_domain(record)

    def save(self, run: EngineeringAnswerRun) -> None:
        record = self._session.get(EngineeringAnswerRunRecord, run.answer_run_id.value)
        if record is None:
            self._session.add(AnswerRunMapper.to_record(run))
        else:
            AnswerRunMapper.apply_to_record(run, record)
        self._session.execute(
            delete(EngineeringAnswerCitationRecord).where(
                EngineeringAnswerCitationRecord.answer_run_id == run.answer_run_id.value
            )
        )
        for citation in AnswerRunMapper.to_citation_records(run):
            self._session.add(citation)
        self._session.flush()

    def find_by_projection_key(self, projection_key: str) -> EngineeringAnswerRun | None:
        record = self._session.scalars(
            select(EngineeringAnswerRunRecord).where(
                EngineeringAnswerRunRecord.projection_key == projection_key.strip(),
                EngineeringAnswerRunRecord.status == AnswerStatus.COMPLETED.value,
            )
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def list_by_repository(
        self,
        repository_id: RepositoryId,
        *,
        limit: int = 50,
    ) -> tuple[EngineeringAnswerRun, ...]:
        records = self._session.scalars(
            select(EngineeringAnswerRunRecord)
            .where(EngineeringAnswerRunRecord.repository_id == repository_id.value)
            .order_by(EngineeringAnswerRunRecord.created_at.desc())
            .limit(max(1, limit))
        ).all()
        return tuple(self._to_domain(item) for item in records)

    def _to_domain(self, record: EngineeringAnswerRunRecord) -> EngineeringAnswerRun:
        citations = list(
            self._session.scalars(
                select(EngineeringAnswerCitationRecord).where(
                    EngineeringAnswerCitationRecord.answer_run_id == record.id
                )
            ).all()
        )
        return AnswerRunMapper.to_domain(record, citations)
