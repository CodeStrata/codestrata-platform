"""SqlAlchemy portfolio answer run repository."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from codestrata_platform.domain.answering.lifecycle import AnswerStatus
from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio_answering.answer import PortfolioAnswerRun
from codestrata_platform.domain.portfolio_answering.identifiers import PortfolioAnswerRunId
from codestrata_platform.infrastructure.persistence.mappers.portfolio_answer_mapper import (
    PortfolioAnswerRunMapper,
)
from codestrata_platform.infrastructure.persistence.models.portfolio_answer_records import (
    EngineeringPortfolioAnswerCitationRecord,
    EngineeringPortfolioAnswerFeedbackRecord,
    EngineeringPortfolioAnswerRunRecord,
)


class SqlAlchemyPortfolioAnswerRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, answer_run_id: PortfolioAnswerRunId) -> PortfolioAnswerRun | None:
        record = self._session.get(EngineeringPortfolioAnswerRunRecord, answer_run_id.value)
        if record is None:
            return None
        return self._to_domain(record)

    def save(self, run: PortfolioAnswerRun) -> None:
        record = self._session.get(EngineeringPortfolioAnswerRunRecord, run.answer_run_id.value)
        if record is None:
            self._session.add(PortfolioAnswerRunMapper.to_record(run))
        else:
            PortfolioAnswerRunMapper.apply_to_record(run, record)
        self._session.execute(
            delete(EngineeringPortfolioAnswerCitationRecord).where(
                EngineeringPortfolioAnswerCitationRecord.answer_run_id == run.answer_run_id.value
            )
        )
        for citation in PortfolioAnswerRunMapper.to_citation_records(run):
            self._session.add(citation)
        self._session.flush()

    def find_by_projection_key(self, projection_key: str) -> PortfolioAnswerRun | None:
        record = self._session.scalars(
            select(EngineeringPortfolioAnswerRunRecord).where(
                EngineeringPortfolioAnswerRunRecord.projection_key == projection_key.strip(),
                EngineeringPortfolioAnswerRunRecord.status == AnswerStatus.COMPLETED.value,
            )
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
        *,
        limit: int = 50,
    ) -> tuple[PortfolioAnswerRun, ...]:
        records = self._session.scalars(
            select(EngineeringPortfolioAnswerRunRecord)
            .where(EngineeringPortfolioAnswerRunRecord.portfolio_id == portfolio_id.value)
            .order_by(EngineeringPortfolioAnswerRunRecord.created_at.desc())
            .limit(max(1, limit))
        ).all()
        return tuple(self._to_domain(item) for item in records)

    def save_feedback(
        self,
        *,
        answer_run_id: PortfolioAnswerRunId,
        rating: int,
        feedback_category: str,
        comment: str,
    ) -> dict[str, object]:
        now = datetime.now(UTC)
        token = hashlib.sha256(
            f"{answer_run_id.value}|{rating}|{feedback_category}|{comment}|{now.isoformat()}".encode()
        ).hexdigest()[:24]
        feedback_id = f"portfolio-answer-feedback:{token}"
        record = EngineeringPortfolioAnswerFeedbackRecord(
            id=feedback_id,
            answer_run_id=answer_run_id.value,
            rating=rating,
            feedback_category=feedback_category[:64],
            comment=comment[:1000],
            created_at=now,
        )
        self._session.add(record)
        self._session.flush()
        return {
            "id": feedback_id,
            "answer_run_id": answer_run_id.value,
            "rating": rating,
            "feedback_category": feedback_category[:64],
            "comment": comment[:1000],
        }

    def list_feedback(
        self,
        answer_run_id: PortfolioAnswerRunId,
    ) -> tuple[dict[str, object], ...]:
        records = self._session.scalars(
            select(EngineeringPortfolioAnswerFeedbackRecord)
            .where(
                EngineeringPortfolioAnswerFeedbackRecord.answer_run_id == answer_run_id.value
            )
            .order_by(EngineeringPortfolioAnswerFeedbackRecord.created_at.asc())
        ).all()
        return tuple(
            {
                "id": item.id,
                "answer_run_id": item.answer_run_id,
                "rating": item.rating,
                "feedback_category": item.feedback_category,
                "comment": item.comment,
            }
            for item in records
        )

    def _to_domain(
        self,
        record: EngineeringPortfolioAnswerRunRecord,
    ) -> PortfolioAnswerRun:
        citations = list(
            self._session.scalars(
                select(EngineeringPortfolioAnswerCitationRecord).where(
                    EngineeringPortfolioAnswerCitationRecord.answer_run_id == record.id
                )
            ).all()
        )
        return PortfolioAnswerRunMapper.to_domain(record, citations)
