"""In-memory Executive Intelligence repository."""

from __future__ import annotations

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


class InMemoryExecutiveIntelligenceRepository:
    def __init__(self) -> None:
        self._items: dict[str, ExecutiveIntelligenceSnapshot] = {}

    def get(
        self,
        executive_intelligence_id: ExecutiveIntelligenceId,
    ) -> ExecutiveIntelligenceSnapshot | None:
        item = self._items.get(executive_intelligence_id.value)
        return item.snapshot() if item is not None else None

    def save(self, snapshot: ExecutiveIntelligenceSnapshot) -> None:
        self._items[snapshot.executive_intelligence_id.value] = snapshot.snapshot()

    def find_completed_by_projection_key(
        self,
        projection_key: str,
    ) -> ExecutiveIntelligenceSnapshot | None:
        key = projection_key.strip()
        matches = [
            item
            for item in self._items.values()
            if item.projection_key.value == key
            and item.status is ExecutiveIntelligenceStatus.COMPLETED
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: item.version.value).snapshot()

    def latest_completed_for_portfolio(
        self,
        portfolio_id: PortfolioId,
    ) -> ExecutiveIntelligenceSnapshot | None:
        matches = [
            item
            for item in self._items.values()
            if item.portfolio_id == portfolio_id
            and item.status is ExecutiveIntelligenceStatus.COMPLETED
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: item.version.value).snapshot()

    def latest_completed_for_portfolio_snapshot(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
    ) -> ExecutiveIntelligenceSnapshot | None:
        matches = [
            item
            for item in self._items.values()
            if item.portfolio_snapshot_id == portfolio_snapshot_id
            and item.status is ExecutiveIntelligenceStatus.COMPLETED
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: item.version.value).snapshot()

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
        *,
        limit: int = 50,
    ) -> tuple[ExecutiveIntelligenceSnapshot, ...]:
        items = [
            item.snapshot()
            for item in self._items.values()
            if item.portfolio_id == portfolio_id
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
