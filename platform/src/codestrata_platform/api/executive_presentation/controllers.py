"""Thin Executive Presentation controllers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.executive_presentation.dto import (
    ExecutivePresentationResponse,
    PresentationCtoSummaryDto,
    PresentationExecutiveSummaryDto,
    PresentationScorecardDto,
)
from codestrata_platform.api.executive_presentation.mappers import (
    presentation_cto_summary_response,
    presentation_executive_summary_response,
    presentation_response,
    presentation_scorecard_response,
)
from codestrata_platform.application.executive_presentation.queries import (
    GetExecutivePresentationByPortfolioSnapshotQuery,
    GetExecutivePresentationQuery,
    GetLatestExecutivePresentationQuery,
)
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.workspace.ids import WorkspaceId

router = APIRouter(tags=["Executive Presentation"])


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/presentation",
    response_model=ExecutivePresentationResponse,
)
def get_executive_presentation(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> ExecutivePresentationResponse:
    model = services.executive_presentation.get(
        GetExecutivePresentationQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return presentation_response(model)


@router.get(
    "/portfolios/{portfolio_id}/executive-presentation/latest",
    response_model=ExecutivePresentationResponse,
)
def get_latest_executive_presentation(
    portfolio_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> ExecutivePresentationResponse:
    model = services.executive_presentation.get_latest(
        GetLatestExecutivePresentationQuery(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return presentation_response(model)


@router.get(
    "/portfolio-snapshots/{portfolio_snapshot_id}/executive-presentation",
    response_model=ExecutivePresentationResponse,
)
def get_executive_presentation_by_portfolio_snapshot(
    portfolio_snapshot_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
    portfolio_id: Annotated[str | None, Query()] = None,
) -> ExecutivePresentationResponse:
    model = services.executive_presentation.get_by_portfolio_snapshot(
        GetExecutivePresentationByPortfolioSnapshotQuery(
            portfolio_snapshot_id=PortfolioSnapshotId(portfolio_snapshot_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
            portfolio_id=PortfolioId(portfolio_id) if portfolio_id else None,
        )
    )
    return presentation_response(model)


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/presentation/executive-summary",
    response_model=PresentationExecutiveSummaryDto,
)
def get_executive_presentation_executive_summary(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> PresentationExecutiveSummaryDto:
    model = services.executive_presentation.get(
        GetExecutivePresentationQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return presentation_executive_summary_response(model)


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/presentation/cto-summary",
    response_model=PresentationCtoSummaryDto,
)
def get_executive_presentation_cto_summary(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> PresentationCtoSummaryDto:
    model = services.executive_presentation.get(
        GetExecutivePresentationQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return presentation_cto_summary_response(model)


@router.get(
    "/executive-intelligence/{executive_intelligence_id}/presentation/scorecard",
    response_model=PresentationScorecardDto,
)
def get_executive_presentation_scorecard(
    executive_intelligence_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> PresentationScorecardDto:
    model = services.executive_presentation.get(
        GetExecutivePresentationQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(executive_intelligence_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return presentation_scorecard_response(model)
