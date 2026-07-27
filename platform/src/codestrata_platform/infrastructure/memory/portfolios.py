"""In-memory portfolio repositories."""

from __future__ import annotations

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio.lifecycle import PortfolioSnapshotStatus, PortfolioStatus
from codestrata_platform.domain.portfolio.portfolio import EngineeringPortfolio
from codestrata_platform.domain.portfolio.snapshot import PortfolioSnapshot
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


class InMemoryPortfolioRepository:
    def __init__(self) -> None:
        self._items: dict[str, EngineeringPortfolio] = {}

    def get(self, portfolio_id: PortfolioId) -> EngineeringPortfolio | None:
        item = self._items.get(portfolio_id.value)
        return item.snapshot() if item is not None else None

    def save(self, portfolio: EngineeringPortfolio) -> None:
        self._items[portfolio.portfolio_id.value] = portfolio.snapshot()

    def list_by_workspace(
        self,
        workspace_id: WorkspaceId,
        *,
        status: PortfolioStatus | None = None,
    ) -> tuple[EngineeringPortfolio, ...]:
        items = [
            item.snapshot()
            for item in self._items.values()
            if item.workspace_id == workspace_id and (status is None or item.status is status)
        ]
        items.sort(key=lambda item: item.audit.created_at.value, reverse=True)
        return tuple(items)

    def list_by_organization(
        self,
        organization_id: OrganizationId,
        *,
        status: PortfolioStatus | None = None,
    ) -> tuple[EngineeringPortfolio, ...]:
        items = [
            item.snapshot()
            for item in self._items.values()
            if item.organization_id == organization_id
            and (status is None or item.status is status)
        ]
        items.sort(key=lambda item: item.audit.created_at.value, reverse=True)
        return tuple(items)

    def list_containing_repository(
        self,
        repository_id: RepositoryId,
    ) -> tuple[EngineeringPortfolio, ...]:
        items = [
            item.snapshot()
            for item in self._items.values()
            if any(
                membership.repository_id == repository_id and membership.is_active
                for membership in item.memberships
            )
        ]
        return tuple(items)


class InMemoryPortfolioSnapshotRepository:
    def __init__(self) -> None:
        self._items: dict[str, PortfolioSnapshot] = {}

    def get(self, portfolio_snapshot_id: PortfolioSnapshotId) -> PortfolioSnapshot | None:
        item = self._items.get(portfolio_snapshot_id.value)
        return item.snapshot() if item is not None else None

    def save(self, snapshot: PortfolioSnapshot) -> None:
        existing = self._items.get(snapshot.portfolio_snapshot_id.value)
        if (
            existing is not None
            and existing.status is PortfolioSnapshotStatus.COMPLETED
            and snapshot.status is PortfolioSnapshotStatus.COMPLETED
            and existing._version != snapshot._version
        ):
            # Allow supersede/archive transitions from completed only via status change.
            pass
        if (
            existing is not None
            and existing.status is PortfolioSnapshotStatus.COMPLETED
            and snapshot.status
            not in {
                PortfolioSnapshotStatus.COMPLETED,
                PortfolioSnapshotStatus.SUPERSEDED,
                PortfolioSnapshotStatus.ARCHIVED,
            }
        ):
            raise RuntimeError("Completed portfolio snapshots are immutable")
        self._items[snapshot.portfolio_snapshot_id.value] = snapshot.snapshot()

    def find_completed_by_projection_key(
        self,
        projection_key: str,
    ) -> PortfolioSnapshot | None:
        key = projection_key.strip()
        matches = [
            item
            for item in self._items.values()
            if item.projection_key.value == key
            and item.status is PortfolioSnapshotStatus.COMPLETED
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: item.version.value).snapshot()

    def get_latest_completed(
        self,
        portfolio_id: PortfolioId,
    ) -> PortfolioSnapshot | None:
        matches = [
            item
            for item in self._items.values()
            if item.portfolio_id == portfolio_id
            and item.status is PortfolioSnapshotStatus.COMPLETED
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: item.version.value).snapshot()

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
        *,
        status: PortfolioSnapshotStatus | None = None,
        limit: int = 50,
    ) -> tuple[PortfolioSnapshot, ...]:
        items = [
            item.snapshot()
            for item in self._items.values()
            if item.portfolio_id == portfolio_id and (status is None or item.status is status)
        ]
        items.sort(key=lambda item: item.version.value, reverse=True)
        return tuple(items[: max(1, limit)])

    def latest_version_for_portfolio(self, portfolio_id: PortfolioId) -> int:
        versions = [
            item.version.value
            for item in self._items.values()
            if item.portfolio_id == portfolio_id
        ]
        return max(versions) if versions else 0


class InMemoryPortfolioQueryRepository:
    def __init__(self, snapshots: InMemoryPortfolioSnapshotRepository) -> None:
        self._snapshots = snapshots

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
        snapshot = self._snapshots.get(portfolio_snapshot_id)
        if snapshot is None:
            return ()
        items = list(snapshot.technology_inventory)
        if technology:
            needle = technology.strip().lower()
            items = [
                item
                for item in items
                if getattr(item, "canonical_key", "").lower().find(needle) >= 0
            ]
        if framework:
            needle = framework.strip().lower()
            items = [
                item
                for item in items
                if (getattr(item, "framework", None) or "").lower() == needle
            ]
        return tuple(items[offset : offset + limit])

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
            patterns = [
                item
                for item in patterns
                if getattr(item.category, "value", "") == category.strip().lower()
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
            patterns = [
                item
                for item in patterns
                if getattr(item.category, "value", "") == category.strip().lower()
            ]
        if priority:
            patterns = [
                item for item in patterns if item.priority.lower() == priority.strip().lower()
            ]
        return tuple(patterns[offset : offset + limit])
