"""Thin Strategic Portfolio Roadmap controllers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.strategic_roadmap.dto import (
    RoadmapInitiativesResponse,
    RoadmapSummaryResponse,
    RoadmapWavesResponse,
    StrategicRoadmapResponse,
)
from codestrata_platform.api.strategic_roadmap.mappers import (
    initiatives_response,
    roadmap_response,
    summary_response,
    waves_response,
)
from codestrata_platform.application.strategic_roadmap.queries import (
    GetLatestStrategicRoadmapQuery,
    GetStrategicRoadmapByPortfolioSnapshotQuery,
    GetStrategicRoadmapQuery,
)
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.workspace.ids import WorkspaceId

router = APIRouter(tags=["Strategic Portfolio Roadmap"])


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/roadmap",
    response_model=StrategicRoadmapResponse,
)
def get_strategic_roadmap(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str | None, Query()] = None,
    workspace_id: Annotated[str | None, Query()] = None,
) -> StrategicRoadmapResponse:
    model = services.strategic_roadmap.get(
        GetStrategicRoadmapQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id) if organization_id else None,
            workspace_id=WorkspaceId(workspace_id) if workspace_id else None,
        )
    )
    return roadmap_response(model)


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/roadmap/initiatives",
    response_model=RoadmapInitiativesResponse,
)
def get_strategic_roadmap_initiatives(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str | None, Query()] = None,
    workspace_id: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    wave: Annotated[str | None, Query()] = None,
) -> RoadmapInitiativesResponse:
    model = services.strategic_roadmap.get(
        GetStrategicRoadmapQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id) if organization_id else None,
            workspace_id=WorkspaceId(workspace_id) if workspace_id else None,
        )
    )
    return initiatives_response(model, category=category, wave=wave)


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/roadmap/waves",
    response_model=RoadmapWavesResponse,
)
def get_strategic_roadmap_waves(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str | None, Query()] = None,
    workspace_id: Annotated[str | None, Query()] = None,
) -> RoadmapWavesResponse:
    model = services.strategic_roadmap.get(
        GetStrategicRoadmapQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id) if organization_id else None,
            workspace_id=WorkspaceId(workspace_id) if workspace_id else None,
        )
    )
    return waves_response(model)


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/roadmap/summary",
    response_model=RoadmapSummaryResponse,
)
def get_strategic_roadmap_summary(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str | None, Query()] = None,
    workspace_id: Annotated[str | None, Query()] = None,
) -> RoadmapSummaryResponse:
    model = services.strategic_roadmap.get(
        GetStrategicRoadmapQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id) if organization_id else None,
            workspace_id=WorkspaceId(workspace_id) if workspace_id else None,
        )
    )
    return summary_response(model)


@router.get(
    "/portfolios/{portfolio_id}/roadmap/latest",
    response_model=StrategicRoadmapResponse,
)
def get_latest_strategic_roadmap(
    portfolio_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> StrategicRoadmapResponse:
    model = services.strategic_roadmap.get_latest(
        GetLatestStrategicRoadmapQuery(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return roadmap_response(model)


@router.get(
    "/portfolio-snapshots/{portfolio_snapshot_id}/roadmap",
    response_model=StrategicRoadmapResponse,
)
def get_strategic_roadmap_by_portfolio_snapshot(
    portfolio_snapshot_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
    portfolio_id: Annotated[str | None, Query()] = None,
) -> StrategicRoadmapResponse:
    model = services.strategic_roadmap.get_by_portfolio_snapshot(
        GetStrategicRoadmapByPortfolioSnapshotQuery(
            portfolio_snapshot_id=PortfolioSnapshotId(portfolio_snapshot_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
            portfolio_id=PortfolioId(portfolio_id) if portfolio_id else None,
        )
    )
    return roadmap_response(model)
