"""SqlAlchemy Executive Intelligence persistence repository."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveIntelligenceStatus,
)
from codestrata_platform.domain.executive_intelligence.snapshot import (
    ExecutiveIntelligenceSnapshot,
)
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.infrastructure.persistence.mappers.executive_intelligence_mapper import (
    ExecutiveIntelligenceMapper,
)
from codestrata_platform.infrastructure.persistence.models.executive_intelligence_records import (
    EngineeringExecutiveFindingRecord,
    EngineeringExecutiveIntelligenceSnapshotRecord,
    EngineeringExecutiveMetricRecord,
    EngineeringExecutiveObservationRecord,
    EngineeringExecutiveRecommendationRecord,
)

_CHILD_TYPES = (
    EngineeringExecutiveMetricRecord,
    EngineeringExecutiveFindingRecord,
    EngineeringExecutiveRecommendationRecord,
    EngineeringExecutiveObservationRecord,
)


class SqlAlchemyExecutiveIntelligenceRepository:
    """Durable ExecutiveIntelligenceRepository adapter."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(
        self,
        executive_intelligence_id: ExecutiveIntelligenceId,
    ) -> ExecutiveIntelligenceSnapshot | None:
        record = self._session.get(
            EngineeringExecutiveIntelligenceSnapshotRecord,
            executive_intelligence_id.value,
        )
        if record is None:
            return None
        return self._to_domain(record)

    def save(self, snapshot: ExecutiveIntelligenceSnapshot) -> None:
        exec_id = snapshot.executive_intelligence_id.value
        existing = self._session.get(EngineeringExecutiveIntelligenceSnapshotRecord, exec_id)
        if existing is None:
            self._session.add(ExecutiveIntelligenceMapper.to_snapshot_record(snapshot))
        else:
            ExecutiveIntelligenceMapper.apply_snapshot_to_record(snapshot, existing)

        for child_type in _CHILD_TYPES:
            self._session.execute(
                delete(child_type).where(child_type.executive_intelligence_id == exec_id)
            )
        for child in (
            *ExecutiveIntelligenceMapper.to_metric_records(snapshot),
            *ExecutiveIntelligenceMapper.to_finding_records(snapshot),
            *ExecutiveIntelligenceMapper.to_recommendation_records(snapshot),
            *ExecutiveIntelligenceMapper.to_observation_records(snapshot),
        ):
            self._session.add(child)
        self._session.flush()

    def find_completed_by_projection_key(
        self,
        projection_key: str,
    ) -> ExecutiveIntelligenceSnapshot | None:
        record = self._session.scalars(
            select(EngineeringExecutiveIntelligenceSnapshotRecord)
            .where(
                EngineeringExecutiveIntelligenceSnapshotRecord.projection_key
                == projection_key.strip(),
                EngineeringExecutiveIntelligenceSnapshotRecord.status
                == ExecutiveIntelligenceStatus.COMPLETED.value,
            )
            .order_by(EngineeringExecutiveIntelligenceSnapshotRecord.version.desc())
            .limit(1)
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def latest_completed_for_portfolio(
        self,
        portfolio_id: PortfolioId,
    ) -> ExecutiveIntelligenceSnapshot | None:
        record = self._session.scalars(
            select(EngineeringExecutiveIntelligenceSnapshotRecord)
            .where(
                EngineeringExecutiveIntelligenceSnapshotRecord.portfolio_id
                == portfolio_id.value,
                EngineeringExecutiveIntelligenceSnapshotRecord.status
                == ExecutiveIntelligenceStatus.COMPLETED.value,
            )
            .order_by(EngineeringExecutiveIntelligenceSnapshotRecord.version.desc())
            .limit(1)
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def latest_completed_for_portfolio_snapshot(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
    ) -> ExecutiveIntelligenceSnapshot | None:
        record = self._session.scalars(
            select(EngineeringExecutiveIntelligenceSnapshotRecord)
            .where(
                EngineeringExecutiveIntelligenceSnapshotRecord.portfolio_snapshot_id
                == portfolio_snapshot_id.value,
                EngineeringExecutiveIntelligenceSnapshotRecord.status
                == ExecutiveIntelligenceStatus.COMPLETED.value,
            )
            .order_by(EngineeringExecutiveIntelligenceSnapshotRecord.version.desc())
            .limit(1)
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[ExecutiveIntelligenceSnapshot, ...]:
        records = list(
            self._session.scalars(
                select(EngineeringExecutiveIntelligenceSnapshotRecord)
                .where(
                    EngineeringExecutiveIntelligenceSnapshotRecord.portfolio_id
                    == portfolio_id.value
                )
                .order_by(EngineeringExecutiveIntelligenceSnapshotRecord.version.desc())
                .offset(max(0, offset))
                .limit(max(1, limit))
            ).all()
        )
        return self._to_domain_many(records)

    def count_by_portfolio(self, portfolio_id: PortfolioId) -> int:
        value = self._session.scalar(
            select(func.count())
            .select_from(EngineeringExecutiveIntelligenceSnapshotRecord)
            .where(
                EngineeringExecutiveIntelligenceSnapshotRecord.portfolio_id
                == portfolio_id.value
            )
        )
        return int(value or 0)

    def latest_version_for_portfolio(self, portfolio_id: PortfolioId) -> int:
        value = self._session.scalar(
            select(func.max(EngineeringExecutiveIntelligenceSnapshotRecord.version)).where(
                EngineeringExecutiveIntelligenceSnapshotRecord.portfolio_id == portfolio_id.value
            )
        )
        return int(value or 0)

    def _to_domain(
        self,
        record: EngineeringExecutiveIntelligenceSnapshotRecord,
    ) -> ExecutiveIntelligenceSnapshot:
        return self._to_domain_many([record])[0]

    def _to_domain_many(
        self,
        records: list[EngineeringExecutiveIntelligenceSnapshotRecord],
    ) -> tuple[ExecutiveIntelligenceSnapshot, ...]:
        if not records:
            return ()
        ids = [record.executive_intelligence_id for record in records]
        metrics_by_id: dict[str, list[EngineeringExecutiveMetricRecord]] = {
            item: [] for item in ids
        }
        findings_by_id: dict[str, list[EngineeringExecutiveFindingRecord]] = {
            item: [] for item in ids
        }
        recommendations_by_id: dict[str, list[EngineeringExecutiveRecommendationRecord]] = {
            item: [] for item in ids
        }
        observations_by_id: dict[str, list[EngineeringExecutiveObservationRecord]] = {
            item: [] for item in ids
        }
        for row in self._session.scalars(
            select(EngineeringExecutiveMetricRecord).where(
                EngineeringExecutiveMetricRecord.executive_intelligence_id.in_(ids)
            )
        ).all():
            metrics_by_id[row.executive_intelligence_id].append(row)
        for row in self._session.scalars(
            select(EngineeringExecutiveFindingRecord).where(
                EngineeringExecutiveFindingRecord.executive_intelligence_id.in_(ids)
            )
        ).all():
            findings_by_id[row.executive_intelligence_id].append(row)
        for row in self._session.scalars(
            select(EngineeringExecutiveRecommendationRecord).where(
                EngineeringExecutiveRecommendationRecord.executive_intelligence_id.in_(ids)
            )
        ).all():
            recommendations_by_id[row.executive_intelligence_id].append(row)
        for row in self._session.scalars(
            select(EngineeringExecutiveObservationRecord).where(
                EngineeringExecutiveObservationRecord.executive_intelligence_id.in_(ids)
            )
        ).all():
            observations_by_id[row.executive_intelligence_id].append(row)
        return tuple(
            ExecutiveIntelligenceMapper.from_records(
                record,
                metric_records=metrics_by_id[record.executive_intelligence_id],
                finding_records=findings_by_id[record.executive_intelligence_id],
                recommendation_records=recommendations_by_id[record.executive_intelligence_id],
                observation_records=observations_by_id[record.executive_intelligence_id],
            )
            for record in records
        )
