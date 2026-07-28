"""SqlAlchemy portfolio persistence repositories."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio.lifecycle import PortfolioSnapshotStatus, PortfolioStatus
from codestrata_platform.domain.portfolio.portfolio import EngineeringPortfolio
from codestrata_platform.domain.portfolio.snapshot import PortfolioSnapshot
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers.portfolio_mapper import PortfolioMapper
from codestrata_platform.infrastructure.persistence.models.portfolio_records import (
    EngineeringPortfolioAnalysisRunRecord,
    EngineeringPortfolioFindingRecord,
    EngineeringPortfolioMembershipRecord,
    EngineeringPortfolioModernizationCandidateRecord,
    EngineeringPortfolioRecommendationRecord,
    EngineeringPortfolioRecord,
    EngineeringPortfolioRepositorySnapshotRecord,
    EngineeringPortfolioRiskRecord,
    EngineeringPortfolioSnapshotRecord,
    EngineeringPortfolioTechnologyRecord,
)

_SNAPSHOT_CHILD_TYPES = (
    EngineeringPortfolioRepositorySnapshotRecord,
    EngineeringPortfolioTechnologyRecord,
    EngineeringPortfolioFindingRecord,
    EngineeringPortfolioRecommendationRecord,
    EngineeringPortfolioRiskRecord,
    EngineeringPortfolioModernizationCandidateRecord,
)

_COMPLETED_ALLOWED_TRANSITIONS = frozenset(
    {
        PortfolioSnapshotStatus.COMPLETED,
        PortfolioSnapshotStatus.SUPERSEDED,
        PortfolioSnapshotStatus.ARCHIVED,
    }
)


class SqlAlchemyPortfolioRepository:
    """Durable EngineeringPortfolioRepository adapter."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, portfolio_id: PortfolioId) -> EngineeringPortfolio | None:
        record = self._session.get(EngineeringPortfolioRecord, portfolio_id.value)
        if record is None:
            return None
        return self._to_domain(record)

    def save(self, portfolio: EngineeringPortfolio) -> None:
        record = self._session.get(EngineeringPortfolioRecord, portfolio.portfolio_id.value)
        portfolio_record, memberships = PortfolioMapper.to_portfolio_record(portfolio)
        if record is None:
            self._session.add(portfolio_record)
        else:
            PortfolioMapper.apply_portfolio_to_record(portfolio, record)

        portfolio_id = portfolio.portfolio_id.value
        self._session.execute(
            delete(EngineeringPortfolioMembershipRecord).where(
                EngineeringPortfolioMembershipRecord.portfolio_id == portfolio_id
            )
        )
        for membership in memberships:
            self._session.add(membership)
        self._session.flush()

    def list_by_workspace(
        self,
        workspace_id: WorkspaceId,
        *,
        status: PortfolioStatus | None = None,
    ) -> tuple[EngineeringPortfolio, ...]:
        stmt = select(EngineeringPortfolioRecord).where(
            EngineeringPortfolioRecord.workspace_id == workspace_id.value
        )
        if status is not None:
            stmt = stmt.where(EngineeringPortfolioRecord.status == status.value)
        records = self._session.scalars(
            stmt.order_by(EngineeringPortfolioRecord.created_at.desc())
        ).all()
        return tuple(self._to_domain(record) for record in records)

    def list_by_organization(
        self,
        organization_id: OrganizationId,
        *,
        status: PortfolioStatus | None = None,
    ) -> tuple[EngineeringPortfolio, ...]:
        stmt = select(EngineeringPortfolioRecord).where(
            EngineeringPortfolioRecord.organization_id == organization_id.value
        )
        if status is not None:
            stmt = stmt.where(EngineeringPortfolioRecord.status == status.value)
        records = self._session.scalars(
            stmt.order_by(EngineeringPortfolioRecord.created_at.desc())
        ).all()
        return tuple(self._to_domain(record) for record in records)

    def list_containing_repository(
        self,
        repository_id: RepositoryId,
    ) -> tuple[EngineeringPortfolio, ...]:
        portfolio_ids = self._session.scalars(
            select(EngineeringPortfolioMembershipRecord.portfolio_id).where(
                EngineeringPortfolioMembershipRecord.repository_id == repository_id.value,
                EngineeringPortfolioMembershipRecord.removed_at.is_(None),
            )
        ).all()
        if not portfolio_ids:
            return ()
        records = self._session.scalars(
            select(EngineeringPortfolioRecord).where(
                EngineeringPortfolioRecord.portfolio_id.in_(tuple(portfolio_ids))
            )
        ).all()
        return tuple(self._to_domain(record) for record in records)

    def _to_domain(self, record: EngineeringPortfolioRecord) -> EngineeringPortfolio:
        memberships = list(
            self._session.scalars(
                select(EngineeringPortfolioMembershipRecord).where(
                    EngineeringPortfolioMembershipRecord.portfolio_id == record.portfolio_id
                )
            ).all()
        )
        return PortfolioMapper.from_portfolio_record(record, memberships)


class SqlAlchemyPortfolioSnapshotRepository:
    """Durable PortfolioSnapshotRepository adapter."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, portfolio_snapshot_id: PortfolioSnapshotId) -> PortfolioSnapshot | None:
        record = self._session.get(
            EngineeringPortfolioSnapshotRecord, portfolio_snapshot_id.value
        )
        if record is None:
            return None
        return self._to_domain(record)

    def save(self, snapshot: PortfolioSnapshot) -> None:
        existing = self._session.get(
            EngineeringPortfolioSnapshotRecord, snapshot.portfolio_snapshot_id.value
        )
        if existing is not None:
            self._enforce_completed_immutability(existing, snapshot)

        (
            snapshot_record,
            repo_records,
            tech_records,
            finding_records,
            recommendation_records,
            risk_record,
            modernization_records,
            analysis_run,
        ) = PortfolioMapper.to_snapshot_records(snapshot)

        if existing is None:
            self._session.add(snapshot_record)
        else:
            PortfolioMapper.apply_snapshot_to_record(snapshot, existing)

        snap_id = snapshot.portfolio_snapshot_id.value
        for child_type in _SNAPSHOT_CHILD_TYPES:
            self._session.execute(
                delete(child_type).where(child_type.portfolio_snapshot_id == snap_id)
            )
        self._session.execute(
            delete(EngineeringPortfolioAnalysisRunRecord).where(
                EngineeringPortfolioAnalysisRunRecord.portfolio_snapshot_id == snap_id
            )
        )

        for child in (
            *repo_records,
            *tech_records,
            *finding_records,
            *recommendation_records,
            *modernization_records,
        ):
            self._session.add(child)
        if risk_record is not None:
            self._session.add(risk_record)

        if analysis_run is not None:
            self._session.add(analysis_run)
        self._session.flush()

    def find_completed_by_projection_key(
        self,
        projection_key: str,
    ) -> PortfolioSnapshot | None:
        record = self._session.scalars(
            select(EngineeringPortfolioSnapshotRecord)
            .where(
                EngineeringPortfolioSnapshotRecord.projection_key == projection_key.strip(),
                EngineeringPortfolioSnapshotRecord.status
                == PortfolioSnapshotStatus.COMPLETED.value,
            )
            .order_by(EngineeringPortfolioSnapshotRecord.snapshot_version.desc())
            .limit(1)
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def get_latest_completed(
        self,
        portfolio_id: PortfolioId,
    ) -> PortfolioSnapshot | None:
        record = self._session.scalars(
            select(EngineeringPortfolioSnapshotRecord)
            .where(
                EngineeringPortfolioSnapshotRecord.portfolio_id == portfolio_id.value,
                EngineeringPortfolioSnapshotRecord.status
                == PortfolioSnapshotStatus.COMPLETED.value,
            )
            .order_by(EngineeringPortfolioSnapshotRecord.snapshot_version.desc())
            .limit(1)
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
        *,
        status: PortfolioSnapshotStatus | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[PortfolioSnapshot, ...]:
        stmt = select(EngineeringPortfolioSnapshotRecord).where(
            EngineeringPortfolioSnapshotRecord.portfolio_id == portfolio_id.value
        )
        if status is not None:
            stmt = stmt.where(EngineeringPortfolioSnapshotRecord.status == status.value)
        records = list(
            self._session.scalars(
                stmt.order_by(EngineeringPortfolioSnapshotRecord.snapshot_version.desc())
                .offset(max(0, offset))
                .limit(max(1, limit))
            ).all()
        )
        return self._to_domain_many(records)

    def count_by_portfolio(
        self,
        portfolio_id: PortfolioId,
        *,
        status: PortfolioSnapshotStatus | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(EngineeringPortfolioSnapshotRecord)
            .where(EngineeringPortfolioSnapshotRecord.portfolio_id == portfolio_id.value)
        )
        if status is not None:
            stmt = stmt.where(EngineeringPortfolioSnapshotRecord.status == status.value)
        return int(self._session.scalar(stmt) or 0)

    def latest_version_for_portfolio(self, portfolio_id: PortfolioId) -> int:
        value = self._session.scalar(
            select(func.max(EngineeringPortfolioSnapshotRecord.snapshot_version)).where(
                EngineeringPortfolioSnapshotRecord.portfolio_id == portfolio_id.value
            )
        )
        return int(value or 0)

    def _enforce_completed_immutability(
        self,
        existing: EngineeringPortfolioSnapshotRecord,
        snapshot: PortfolioSnapshot,
    ) -> None:
        if existing.status != PortfolioSnapshotStatus.COMPLETED.value:
            return
        if snapshot.status not in _COMPLETED_ALLOWED_TRANSITIONS:
            raise RuntimeError("Completed portfolio snapshots are immutable")
        if snapshot.status is PortfolioSnapshotStatus.COMPLETED:
            current = self._to_domain(existing)
            if self._inventory_fingerprint(current) != self._inventory_fingerprint(snapshot):
                raise RuntimeError(
                    "Completed portfolio snapshot inventories are immutable; "
                    "only SUPERSEDED/ARCHIVED status transitions are allowed"
                )

    @staticmethod
    def _inventory_fingerprint(snapshot: PortfolioSnapshot) -> tuple[object, ...]:
        return (
            len(snapshot.repository_selections),
            len(snapshot.technology_inventory),
            len(snapshot.finding_inventory),
            len(snapshot.recommendation_inventory),
            snapshot.risk_summary is not None,
            snapshot.modernization_summary is not None,
            snapshot.coverage_summary is not None,
            len(snapshot.dependency_signals),
            snapshot.projection_key.value,
            snapshot.aggregation_policy_version.value,
        )

    def _to_domain(self, record: EngineeringPortfolioSnapshotRecord) -> PortfolioSnapshot:
        return self._to_domain_many([record])[0]

    def _to_domain_many(
        self,
        records: list[EngineeringPortfolioSnapshotRecord],
    ) -> tuple[PortfolioSnapshot, ...]:
        if not records:
            return ()
        ids = [record.portfolio_snapshot_id for record in records]
        repos_by_id: dict[str, list[EngineeringPortfolioRepositorySnapshotRecord]] = {
            item: [] for item in ids
        }
        techs_by_id: dict[str, list[EngineeringPortfolioTechnologyRecord]] = {
            item: [] for item in ids
        }
        findings_by_id: dict[str, list[EngineeringPortfolioFindingRecord]] = {
            item: [] for item in ids
        }
        recommendations_by_id: dict[str, list[EngineeringPortfolioRecommendationRecord]] = {
            item: [] for item in ids
        }
        risks_by_id: dict[str, EngineeringPortfolioRiskRecord | None] = {
            item: None for item in ids
        }
        modernization_by_id: dict[
            str, list[EngineeringPortfolioModernizationCandidateRecord]
        ] = {item: [] for item in ids}
        analysis_by_id: dict[str, EngineeringPortfolioAnalysisRunRecord | None] = {
            item: None for item in ids
        }

        for row in self._session.scalars(
            select(EngineeringPortfolioRepositorySnapshotRecord).where(
                EngineeringPortfolioRepositorySnapshotRecord.portfolio_snapshot_id.in_(ids)
            )
        ).all():
            repos_by_id[row.portfolio_snapshot_id].append(row)
        for row in self._session.scalars(
            select(EngineeringPortfolioTechnologyRecord).where(
                EngineeringPortfolioTechnologyRecord.portfolio_snapshot_id.in_(ids)
            )
        ).all():
            techs_by_id[row.portfolio_snapshot_id].append(row)
        for row in self._session.scalars(
            select(EngineeringPortfolioFindingRecord).where(
                EngineeringPortfolioFindingRecord.portfolio_snapshot_id.in_(ids)
            )
        ).all():
            findings_by_id[row.portfolio_snapshot_id].append(row)
        for row in self._session.scalars(
            select(EngineeringPortfolioRecommendationRecord).where(
                EngineeringPortfolioRecommendationRecord.portfolio_snapshot_id.in_(ids)
            )
        ).all():
            recommendations_by_id[row.portfolio_snapshot_id].append(row)
        for row in self._session.scalars(
            select(EngineeringPortfolioRiskRecord).where(
                EngineeringPortfolioRiskRecord.portfolio_snapshot_id.in_(ids)
            )
        ).all():
            risks_by_id[row.portfolio_snapshot_id] = row
        for row in self._session.scalars(
            select(EngineeringPortfolioModernizationCandidateRecord).where(
                EngineeringPortfolioModernizationCandidateRecord.portfolio_snapshot_id.in_(ids)
            )
        ).all():
            modernization_by_id[row.portfolio_snapshot_id].append(row)
        for row in self._session.scalars(
            select(EngineeringPortfolioAnalysisRunRecord).where(
                EngineeringPortfolioAnalysisRunRecord.portfolio_snapshot_id.in_(ids)
            )
        ).all():
            analysis_by_id[row.portfolio_snapshot_id] = row

        return tuple(
            PortfolioMapper.from_snapshot_records(
                record,
                repository_records=repos_by_id[record.portfolio_snapshot_id],
                technology_records=techs_by_id[record.portfolio_snapshot_id],
                finding_records=findings_by_id[record.portfolio_snapshot_id],
                recommendation_records=recommendations_by_id[record.portfolio_snapshot_id],
                risk_record=risks_by_id[record.portfolio_snapshot_id],
                modernization_records=modernization_by_id[record.portfolio_snapshot_id],
                analysis_run=analysis_by_id[record.portfolio_snapshot_id],
            )
            for record in records
        )


class SqlAlchemyPortfolioQueryRepository:
    """Read-side portfolio inventory queries over persisted snapshots."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._snapshots = SqlAlchemyPortfolioSnapshotRepository(session)

    def get_snapshot(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
    ) -> PortfolioSnapshot | None:
        return self._snapshots.get(portfolio_snapshot_id)

    def list_technologies(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
        *,
        technology: str | None = None,
        framework: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[object, ...]:
        stmt = select(EngineeringPortfolioTechnologyRecord).where(
            EngineeringPortfolioTechnologyRecord.portfolio_snapshot_id
            == portfolio_snapshot_id.value
        )
        if technology:
            needle = f"%{technology.strip().lower()}%"
            stmt = stmt.where(
                func.lower(EngineeringPortfolioTechnologyRecord.canonical_key).like(needle)
            )
        if framework:
            stmt = stmt.where(
                func.lower(EngineeringPortfolioTechnologyRecord.framework)
                == framework.strip().lower()
            )
        records = self._session.scalars(stmt.offset(max(0, offset)).limit(max(1, limit))).all()
        return tuple(
            PortfolioMapper._technology_from_record(record)  # noqa: SLF001
            for record in records
        )

    def list_findings(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
        *,
        category: str | None = None,
        severity: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[object, ...]:
        snapshot = self._snapshots.get(portfolio_snapshot_id)
        if snapshot is None or not snapshot.finding_inventory:
            return ()
        summary = snapshot.finding_inventory[0]
        patterns = list(getattr(summary, "recurring_patterns", ()))
        if category:
            needle = category.strip().lower()
            patterns = [
                item
                for item in patterns
                if getattr(item.category, "value", "") == needle
            ]
        if severity:
            needle = severity.strip().lower()
            patterns = [
                item
                for item in patterns
                if any(
                    getattr(dist.severity, "value", "") == needle and dist.count > 0
                    for dist in getattr(item, "severity_distribution", ())
                )
            ]
        return tuple(patterns[offset : offset + limit])

    def list_recommendations(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
        *,
        category: str | None = None,
        priority: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[object, ...]:
        snapshot = self._snapshots.get(portfolio_snapshot_id)
        if snapshot is None or not snapshot.recommendation_inventory:
            return ()
        summary = snapshot.recommendation_inventory[0]
        patterns = list(getattr(summary, "recurring_patterns", ()))
        if category:
            needle = category.strip().lower()
            patterns = [
                item
                for item in patterns
                if getattr(item.category, "value", "") == needle
            ]
        if priority:
            needle = priority.strip().lower()
            patterns = [item for item in patterns if item.priority.lower() == needle]
        return tuple(patterns[offset : offset + limit])
