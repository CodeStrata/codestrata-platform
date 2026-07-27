"""Default Portfolio Retrieval source-snapshot adapter.

Loads a completed ``PortfolioSnapshot`` (and its bounded inventories) via the
Domain ``PortfolioSnapshotRepository`` port, so Portfolio Retrieval indexing
never depends directly on Portfolio persistence internals.
"""

from __future__ import annotations

from codestrata_platform.domain.portfolio.identifiers import PortfolioSnapshotId
from codestrata_platform.domain.portfolio.lifecycle import PortfolioSnapshotStatus
from codestrata_platform.domain.portfolio.ports import PortfolioSnapshotRepository
from codestrata_platform.domain.portfolio_retrieval.ports import PortfolioRetrievalSourceSnapshot


class DefaultPortfolioRetrievalSourceRepository:
    """Bounded read adapter loading a completed PortfolioSnapshot for indexing."""

    def __init__(self, snapshots: PortfolioSnapshotRepository) -> None:
        self._snapshots = snapshots

    def load_completed(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
    ) -> PortfolioRetrievalSourceSnapshot | None:
        snapshot = self._snapshots.get(portfolio_snapshot_id)
        if snapshot is None or snapshot.status is not PortfolioSnapshotStatus.COMPLETED:
            return None
        return PortfolioRetrievalSourceSnapshot(
            portfolio_snapshot=snapshot,
            technology_inventory=snapshot.technology_inventory,
            finding_inventory=snapshot.finding_inventory,
            recommendation_inventory=snapshot.recommendation_inventory,
            risk_summary=snapshot.risk_summary,
            modernization_summary=snapshot.modernization_summary,
            coverage_summary=snapshot.coverage_summary,
            dependency_signals=snapshot.dependency_signals,
        )


__all__ = ["DefaultPortfolioRetrievalSourceRepository"]
