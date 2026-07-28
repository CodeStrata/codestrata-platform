"""Thin Executive Intelligence controllers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.executive_intelligence.dto import (
    BuildExecutiveIntelligenceRequest,
    ExecutiveFindingsResponse,
    ExecutiveIntelligenceDetailsResponse,
    ExecutiveIntelligencePageResponse,
    ExecutiveMetricsResponse,
    ExecutiveRecommendationsResponse,
)
from codestrata_platform.api.executive_intelligence.mappers import (
    details_response,
    findings_response,
    metrics_response,
    page_response,
    recommendations_response,
)
from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_intelligence.queries import (
    GetExecutiveIntelligenceQuery,
    GetLatestExecutiveIntelligenceQuery,
    ListExecutiveIntelligenceQuery,
)
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.workspace.ids import WorkspaceId

router = APIRouter(tags=["Executive Intelligence"])


@router.post(
    "/portfolios/{portfolio_id}/executive-intelligence",
    response_model=ExecutiveIntelligenceDetailsResponse,
    status_code=status.HTTP_201_CREATED,
)
def build_executive_intelligence(
    portfolio_id: str,
    body: BuildExecutiveIntelligenceRequest,
    services: ServicesDep,
) -> ExecutiveIntelligenceDetailsResponse:
    details = services.executive_intelligence.build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(body.organization_id),
            workspace_id=WorkspaceId(body.workspace_id),
            portfolio_snapshot_id=(
                PortfolioSnapshotId(body.portfolio_snapshot_id)
                if body.portfolio_snapshot_id
                else None
            ),
        )
    )
    return details_response(details)


@router.get(
    "/portfolios/{portfolio_id}/executive-intelligence",
    response_model=ExecutiveIntelligencePageResponse,
)
def list_executive_intelligence(
    portfolio_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> ExecutiveIntelligencePageResponse:
    page = services.executive_intelligence.list_by_portfolio(
        ListExecutiveIntelligenceQuery(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
            offset=offset,
            limit=limit,
        )
    )
    return page_response(page)


@router.get(
    "/portfolios/{portfolio_id}/executive-intelligence/latest",
    response_model=ExecutiveIntelligenceDetailsResponse,
)
def latest_executive_intelligence(
    portfolio_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> ExecutiveIntelligenceDetailsResponse:
    details = services.executive_intelligence.get_latest(
        GetLatestExecutiveIntelligenceQuery(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return details_response(details)


@router.get(
    "/executive-intelligence/{executive_intelligence_id}",
    response_model=ExecutiveIntelligenceDetailsResponse,
)
def get_executive_intelligence(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> ExecutiveIntelligenceDetailsResponse:
    details = services.executive_intelligence.get(
        GetExecutiveIntelligenceQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return details_response(details)


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/metrics",
    response_model=ExecutiveMetricsResponse,
)
def get_executive_intelligence_metrics(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> ExecutiveMetricsResponse:
    model = services.executive_intelligence.get_metrics(
        GetExecutiveIntelligenceQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return metrics_response(model)


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/findings",
    response_model=ExecutiveFindingsResponse,
)
def get_executive_intelligence_findings(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> ExecutiveFindingsResponse:
    model = services.executive_intelligence.get_findings(
        GetExecutiveIntelligenceQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return findings_response(model)


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/recommendations",
    response_model=ExecutiveRecommendationsResponse,
)
def get_executive_intelligence_recommendations(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> ExecutiveRecommendationsResponse:
    model = services.executive_intelligence.get_recommendations(
        GetExecutiveIntelligenceQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return recommendations_response(model)


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/overview",
    response_model=ExecutiveIntelligenceDetailsResponse,
)
def get_executive_intelligence_overview(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> ExecutiveIntelligenceDetailsResponse:
    details = services.executive_intelligence.get_overview(
        GetExecutiveIntelligenceQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return details_response(details)
