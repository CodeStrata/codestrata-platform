"""Executive Intelligence application queries."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class GetExecutiveIntelligenceQuery:
    executive_intelligence_id: ExecutiveIntelligenceId
    organization_id: OrganizationId | None = None
    workspace_id: WorkspaceId | None = None


@dataclass(frozen=True, slots=True)
class GetLatestExecutiveIntelligenceQuery:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId


@dataclass(frozen=True, slots=True)
class ListExecutiveIntelligenceQuery:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    offset: int = 0
    limit: int = 50
