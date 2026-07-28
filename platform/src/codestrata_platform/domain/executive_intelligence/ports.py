"""Executive Intelligence repository ports."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.executive_intelligence.snapshot import (
    ExecutiveIntelligenceSnapshot,
)
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId


class ExecutiveIntelligenceRepository(Protocol):
    def get(
        self,
        executive_intelligence_id: ExecutiveIntelligenceId,
    ) -> ExecutiveIntelligenceSnapshot | None: ...

    def save(self, snapshot: ExecutiveIntelligenceSnapshot) -> None: ...

    def find_completed_by_projection_key(
        self,
        projection_key: str,
    ) -> ExecutiveIntelligenceSnapshot | None: ...

    def latest_completed_for_portfolio(
        self,
        portfolio_id: PortfolioId,
    ) -> ExecutiveIntelligenceSnapshot | None: ...

    def latest_completed_for_portfolio_snapshot(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
    ) -> ExecutiveIntelligenceSnapshot | None: ...

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[ExecutiveIntelligenceSnapshot, ...]: ...

    def count_by_portfolio(self, portfolio_id: PortfolioId) -> int: ...

    def latest_version_for_portfolio(self, portfolio_id: PortfolioId) -> int: ...
