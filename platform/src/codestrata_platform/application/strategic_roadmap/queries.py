"""Strategic Portfolio Roadmap application queries."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class GetStrategicRoadmapQuery:
    executive_intelligence_id: ExecutiveIntelligenceId
    organization_id: OrganizationId
    workspace_id: WorkspaceId


@dataclass(frozen=True, slots=True)
class GetLatestStrategicRoadmapQuery:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId


@dataclass(frozen=True, slots=True)
class GetStrategicRoadmapByPortfolioSnapshotQuery:
    portfolio_snapshot_id: PortfolioSnapshotId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    portfolio_id: PortfolioId | None = None
