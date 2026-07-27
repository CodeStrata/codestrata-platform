"""SqlAlchemyEngineeringSnapshotRepository."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.aggregate import EngineeringSnapshot
from codestrata_platform.domain.engineering.enums import EngineeringSnapshotStatus
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.infrastructure.persistence.mappers.engineering_snapshot_mapper import (
    EngineeringSnapshotMapper,
)
from codestrata_platform.infrastructure.persistence.models.engineering_records import (
    EngineeringComponentRecord,
    EngineeringEvidenceRecord,
    EngineeringFindingRecord,
    EngineeringMetricRecord,
    EngineeringRecommendationRecord,
    EngineeringRelationshipRecord,
    EngineeringSnapshotRecord,
    EngineeringTagRecord,
    EngineeringTechnologyRecord,
)

_CHILD_RECORD_TYPES = (
    EngineeringTechnologyRecord,
    EngineeringFindingRecord,
    EngineeringRecommendationRecord,
    EngineeringMetricRecord,
    EngineeringEvidenceRecord,
    EngineeringRelationshipRecord,
    EngineeringTagRecord,
    EngineeringComponentRecord,
)


class SqlAlchemyEngineeringSnapshotRepository:
    """Durable EngineeringSnapshotRepository adapter."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, snapshot_id: EngineeringSnapshotId) -> EngineeringSnapshot | None:
        record = self._session.get(EngineeringSnapshotRecord, snapshot_id.value)
        if record is None:
            return None
        return EngineeringSnapshotMapper.to_domain(record)

    def save(self, snapshot: EngineeringSnapshot) -> None:
        record = self._session.get(EngineeringSnapshotRecord, snapshot.snapshot_id.value)
        if record is None:
            self._session.add(EngineeringSnapshotMapper.to_record(snapshot))
        else:
            EngineeringSnapshotMapper.apply_to_record(snapshot, record)

        snapshot_id = snapshot.snapshot_id.value
        for child_type in _CHILD_RECORD_TYPES:
            self._session.execute(
                delete(child_type).where(child_type.snapshot_id == snapshot_id)
            )

        (
            technologies,
            findings,
            recommendations,
            metrics,
            evidence,
            relationships,
            tags,
            components,
        ) = EngineeringSnapshotMapper.projection_records(snapshot)
        for child in (
            *technologies,
            *findings,
            *recommendations,
            *metrics,
            *evidence,
            *relationships,
            *tags,
            *components,
        ):
            self._session.add(child)
        self._session.flush()

    def list_by_assessment(
        self,
        assessment_id: AssessmentId,
    ) -> tuple[EngineeringSnapshot, ...]:
        records = self._session.scalars(
            select(EngineeringSnapshotRecord)
            .where(EngineeringSnapshotRecord.assessment_id == assessment_id.value)
            .order_by(EngineeringSnapshotRecord.version.asc())
        ).all()
        return tuple(EngineeringSnapshotMapper.to_domain(record) for record in records)

    def get_latest_published(
        self,
        assessment_id: AssessmentId,
    ) -> EngineeringSnapshot | None:
        record = self._session.scalars(
            select(EngineeringSnapshotRecord)
            .where(
                EngineeringSnapshotRecord.assessment_id == assessment_id.value,
                EngineeringSnapshotRecord.status == EngineeringSnapshotStatus.PUBLISHED.value,
            )
            .order_by(EngineeringSnapshotRecord.version.desc())
            .limit(1)
        ).first()
        if record is None:
            return None
        return EngineeringSnapshotMapper.to_domain(record)

    def find_by_intelligence_revision(
        self,
        *,
        assessment_id: AssessmentId,
        assessment_intelligence_id: str,
        assessment_revision: int,
    ) -> EngineeringSnapshot | None:
        record = self._session.scalars(
            select(EngineeringSnapshotRecord).where(
                EngineeringSnapshotRecord.assessment_id == assessment_id.value,
                EngineeringSnapshotRecord.assessment_intelligence_id
                == assessment_intelligence_id.strip(),
                EngineeringSnapshotRecord.assessment_revision == assessment_revision,
            )
        ).first()
        if record is None:
            return None
        return EngineeringSnapshotMapper.to_domain(record)

    def latest_version_for_assessment(self, assessment_id: AssessmentId) -> int:
        value = self._session.scalar(
            select(func.max(EngineeringSnapshotRecord.version)).where(
                EngineeringSnapshotRecord.assessment_id == assessment_id.value
            )
        )
        return int(value or 0)
