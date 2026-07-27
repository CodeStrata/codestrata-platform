"""SqlAlchemyRecommendationRepository."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.intelligence.ids import RecommendationId
from codestrata_platform.domain.intelligence.value_objects import Recommendation
from codestrata_platform.infrastructure.persistence.mappers.assessment_intelligence_mapper import (
    AssessmentIntelligenceMapper,
)
from codestrata_platform.infrastructure.persistence.models.recommendation_finding_link_record import (
    RecommendationFindingLinkRecord,
)
from codestrata_platform.infrastructure.persistence.models.recommendation_record import (
    RecommendationRecord,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_assessment_intelligence_repository import (
    SqlAlchemyAssessmentIntelligenceRepository,
)


class SqlAlchemyRecommendationRepository:
    """Durable RecommendationRepository adapter with assessment-level projection."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, recommendation_id: RecommendationId) -> Recommendation | None:
        record = self._session.get(RecommendationRecord, recommendation_id.value)
        if record is None:
            return None
        related_finding_ids = self._related_finding_ids(record.id)
        return AssessmentIntelligenceMapper.recommendation_to_domain(
            record,
            related_finding_ids=related_finding_ids,
        )

    def list_by_assessment(
        self,
        assessment_id: AssessmentId,
    ) -> tuple[Recommendation, ...]:
        records = self._session.scalars(
            select(RecommendationRecord)
            .where(RecommendationRecord.assessment_id == assessment_id.value)
            .order_by(RecommendationRecord.id.asc())
        ).all()
        recommendations: list[Recommendation] = []
        for record in records:
            recommendations.append(
                AssessmentIntelligenceMapper.recommendation_to_domain(
                    record,
                    related_finding_ids=self._related_finding_ids(record.id),
                )
            )
        return tuple(recommendations)

    def replace_for_assessment(
        self,
        assessment_id: AssessmentId,
        recommendations: tuple[Recommendation, ...],
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
                "Cannot project recommendations without intelligence for assessment "
                f"{assessment_id.value}"
            )

        self._session.execute(
            delete(RecommendationRecord).where(
                RecommendationRecord.assessment_id == assessment_id.value
            )
        )
        for recommendation in recommendations:
            self._session.add(
                AssessmentIntelligenceMapper.recommendation_to_record(
                    recommendation,
                    intelligence_id=resolved_intelligence_id,
                )
            )
        self._session.flush()
        for recommendation in recommendations:
            for finding_id in recommendation.related_finding_ids:
                self._session.add(
                    AssessmentIntelligenceMapper.recommendation_finding_link_to_record(
                        recommendation_id=recommendation.recommendation_id.value,
                        finding_id=finding_id,
                        assessment_id=assessment_id.value,
                    )
                )
        self._session.flush()

    def _related_finding_ids(self, recommendation_id: str) -> tuple[str, ...]:
        rows = self._session.scalars(
            select(RecommendationFindingLinkRecord.finding_id)
            .where(RecommendationFindingLinkRecord.recommendation_id == recommendation_id)
            .order_by(RecommendationFindingLinkRecord.finding_id.asc())
        ).all()
        return tuple(rows)
