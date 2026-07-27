"""SqlAlchemyMetricRepository."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.intelligence.value_objects import Metric
from codestrata_platform.infrastructure.persistence.mappers.assessment_intelligence_mapper import (
    AssessmentIntelligenceMapper,
)
from codestrata_platform.infrastructure.persistence.models.metric_record import MetricRecord
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_assessment_intelligence_repository import (
    SqlAlchemyAssessmentIntelligenceRepository,
)


class SqlAlchemyMetricRepository:
    """Durable MetricRepository adapter with assessment-level projection."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_assessment(self, assessment_id: AssessmentId) -> tuple[Metric, ...]:
        records = self._session.scalars(
            select(MetricRecord)
            .where(MetricRecord.assessment_id == assessment_id.value)
            .order_by(MetricRecord.name.asc())
        ).all()
        return tuple(AssessmentIntelligenceMapper.metric_to_domain(record) for record in records)

    def replace_for_assessment(
        self,
        assessment_id: AssessmentId,
        metrics: tuple[Metric, ...],
        *,
        intelligence_id: str | None = None,
    ) -> None:
        resolved_intelligence_id = intelligence_id or (
            SqlAlchemyAssessmentIntelligenceRepository.latest_intelligence_id_for_assessment(
                self._session,
                assessment_id,
            )
        )
        if resolved_intelligence_id is None:
            raise RuntimeError(
                f"Cannot project metrics without intelligence for assessment {assessment_id.value}"
            )

        self._session.execute(
            delete(MetricRecord).where(MetricRecord.assessment_id == assessment_id.value)
        )
        for metric in metrics:
            self._session.add(
                AssessmentIntelligenceMapper.metric_to_record(
                    metric,
                    assessment_id=assessment_id.value,
                    intelligence_id=resolved_intelligence_id,
                )
            )
        self._session.flush()
