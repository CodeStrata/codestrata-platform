"""Thin Portfolio Intelligence controllers."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Query, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.portfolio.dto import (
    AddRepositoryRequest,
    BuildSnapshotRequest,
    CreatePortfolioRequest,
    PageResponse,
    PortfolioDetailsResponse,
    PortfolioSnapshotDetailsResponse,
    UpdatePortfolioRequest,
)
from codestrata_platform.api.portfolio.mappers import (
    page_response,
    portfolio_details,
    portfolio_summary,
    snapshot_details,
    snapshot_summary,
)
from codestrata_platform.application.portfolio.commands import (
    AddRepositoryToPortfolioCommand,
    ArchivePortfolioCommand,
    BuildPortfolioSnapshotCommand,
    CreatePortfolioCommand,
    RebuildPortfolioSnapshotCommand,
    RemoveRepositoryFromPortfolioCommand,
    UpdatePortfolioCommand,
)
from codestrata_platform.application.portfolio.queries import (
    GetLatestPortfolioSnapshotQuery,
    GetPortfolioQuery,
    GetPortfolioSnapshotQuery,
    ListPortfolioRepositoriesQuery,
    ListPortfolioSnapshotsQuery,
    ListPortfoliosQuery,
    PortfolioInventoryQuery,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio.lifecycle import PortfolioStatus, RepositoryCriticality
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId

router = APIRouter(tags=["Portfolio"])


def _serialize(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(key): _serialize(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(item) for item in obj]
    if hasattr(obj, "value") and not hasattr(obj, "__dataclass_fields__"):
        return obj.value
    if hasattr(obj, "__dataclass_fields__"):
        return {
            field: _serialize(getattr(obj, field))
            for field in obj.__dataclass_fields__
        }
    if hasattr(obj, "value"):
        return obj.value
    return str(obj)


@router.post(
    "/portfolios",
    response_model=PortfolioDetailsResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_portfolio(
    body: CreatePortfolioRequest,
    services: ServicesDep,
) -> PortfolioDetailsResponse:
    details = services.portfolio.management.create_portfolio(
        CreatePortfolioCommand(
            organization_id=OrganizationId(body.organization_id),
            workspace_id=WorkspaceId(body.workspace_id),
            name=body.name,
            description=body.description,
            max_repositories=body.max_repositories,
        )
    )
    return portfolio_details(details)


@router.get("/portfolios", response_model=PageResponse)
def list_portfolios(
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> PageResponse:
    page = services.portfolio.management.list_portfolios(
        ListPortfoliosQuery(
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
            status=PortfolioStatus(status_filter) if status_filter else None,
            offset=offset,
            limit=limit,
        )
    )
    return PageResponse(
        items=[portfolio_summary(item).model_dump() for item in page.items],
        total=page.total,
        offset=page.offset,
        limit=page.limit,
    )


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioDetailsResponse)
def get_portfolio(
    portfolio_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> PortfolioDetailsResponse:
    details = services.portfolio.management.get_portfolio(
        GetPortfolioQuery(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return portfolio_details(details)


@router.patch("/portfolios/{portfolio_id}", response_model=PortfolioDetailsResponse)
def update_portfolio(
    portfolio_id: str,
    body: UpdatePortfolioRequest,
    services: ServicesDep,
) -> PortfolioDetailsResponse:
    details = services.portfolio.management.update_portfolio(
        UpdatePortfolioCommand(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(body.organization_id),
            workspace_id=WorkspaceId(body.workspace_id),
            name=body.name,
            description=body.description,
        )
    )
    return portfolio_details(details)


@router.post(
    "/portfolios/{portfolio_id}/repositories",
    response_model=PortfolioDetailsResponse,
)
def add_repository(
    portfolio_id: str,
    body: AddRepositoryRequest,
    services: ServicesDep,
) -> PortfolioDetailsResponse:
    details = services.portfolio.management.add_repository(
        AddRepositoryToPortfolioCommand(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(body.organization_id),
            workspace_id=WorkspaceId(body.workspace_id),
            repository_id=RepositoryId(body.repository_id),
            criticality=RepositoryCriticality(body.criticality),
            business_capability=body.business_capability,
            owner_reference=body.owner_reference,
            lifecycle_status=body.lifecycle_status,
            tags=tuple(body.tags),
        )
    )
    return portfolio_details(details)


@router.delete(
    "/portfolios/{portfolio_id}/repositories/{repository_id}",
    response_model=PortfolioDetailsResponse,
)
def remove_repository(
    portfolio_id: str,
    repository_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> PortfolioDetailsResponse:
    details = services.portfolio.management.remove_repository(
        RemoveRepositoryFromPortfolioCommand(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
            repository_id=RepositoryId(repository_id),
        )
    )
    return portfolio_details(details)


@router.get("/portfolios/{portfolio_id}/repositories", response_model=PageResponse)
def list_repositories(
    portfolio_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> PageResponse:
    page = services.portfolio.management.list_repositories(
        ListPortfolioRepositoriesQuery(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
            offset=offset,
            limit=limit,
        )
    )
    return page_response(page)


@router.post(
    "/portfolios/{portfolio_id}/snapshots",
    response_model=PortfolioSnapshotDetailsResponse,
    status_code=status.HTTP_201_CREATED,
)
def build_snapshot(
    portfolio_id: str,
    body: BuildSnapshotRequest,
    services: ServicesDep,
) -> PortfolioSnapshotDetailsResponse:
    details = services.portfolio.aggregation.build_snapshot(
        BuildPortfolioSnapshotCommand(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(body.organization_id),
            workspace_id=WorkspaceId(body.workspace_id),
            aggregation_policy_version=body.aggregation_policy_version,
        )
    )
    return snapshot_details(details)


@router.post(
    "/portfolios/{portfolio_id}/snapshots/rebuild",
    response_model=PortfolioSnapshotDetailsResponse,
)
def rebuild_snapshot(
    portfolio_id: str,
    body: BuildSnapshotRequest,
    services: ServicesDep,
) -> PortfolioSnapshotDetailsResponse:
    details = services.portfolio.aggregation.rebuild_snapshot(
        RebuildPortfolioSnapshotCommand(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(body.organization_id),
            workspace_id=WorkspaceId(body.workspace_id),
            aggregation_policy_version=body.aggregation_policy_version,
        )
    )
    return snapshot_details(details)


@router.get("/portfolios/{portfolio_id}/snapshots", response_model=PageResponse)
def list_snapshots(
    portfolio_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> PageResponse:
    page = services.portfolio.aggregation.list_snapshots(
        ListPortfolioSnapshotsQuery(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
            offset=offset,
            limit=limit,
        )
    )
    return PageResponse(
        items=[snapshot_summary(item).model_dump() for item in page.items],
        total=page.total,
        offset=page.offset,
        limit=page.limit,
    )


@router.get(
    "/portfolios/{portfolio_id}/snapshots/latest",
    response_model=PortfolioSnapshotDetailsResponse,
)
def latest_snapshot(
    portfolio_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> PortfolioSnapshotDetailsResponse:
    details = services.portfolio.aggregation.get_latest_snapshot(
        GetLatestPortfolioSnapshotQuery(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return snapshot_details(details)


@router.get(
    "/portfolio-snapshots/{portfolio_snapshot_id}",
    response_model=PortfolioSnapshotDetailsResponse,
)
def get_snapshot(
    portfolio_snapshot_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> PortfolioSnapshotDetailsResponse:
    details = services.portfolio.aggregation.get_snapshot(
        GetPortfolioSnapshotQuery(
            portfolio_snapshot_id=PortfolioSnapshotId(portfolio_snapshot_id),
            organization_id=OrganizationId(organization_id),
            workspace_id=WorkspaceId(workspace_id),
        )
    )
    return snapshot_details(details)


def _inventory_query(
    portfolio_snapshot_id: str,
    *,
    organization_id: str,
    workspace_id: str,
    offset: int,
    limit: int,
    **filters: Any,
) -> PortfolioInventoryQuery:
    return PortfolioInventoryQuery(
        portfolio_snapshot_id=PortfolioSnapshotId(portfolio_snapshot_id),
        organization_id=OrganizationId(organization_id),
        workspace_id=WorkspaceId(workspace_id),
        offset=offset,
        limit=limit,
        **filters,
    )


@router.get("/portfolio-snapshots/{portfolio_snapshot_id}/technologies")
def get_technologies(
    portfolio_snapshot_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
    technology: Annotated[str | None, Query()] = None,
    framework: Annotated[str | None, Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> dict[str, Any]:
    result = services.portfolio.aggregation.get_technologies(
        _inventory_query(
            portfolio_snapshot_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            offset=offset,
            limit=limit,
            technology=technology,
            framework=framework,
        )
    )
    return {
        "envelope": _serialize(result.envelope),
        "items": _serialize(result.items),
        "total": result.total,
    }


@router.get("/portfolio-snapshots/{portfolio_snapshot_id}/findings")
def get_findings(
    portfolio_snapshot_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> dict[str, Any]:
    result = services.portfolio.aggregation.get_findings(
        _inventory_query(
            portfolio_snapshot_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            offset=0,
            limit=50,
        )
    )
    return {"envelope": _serialize(result.envelope), "summary": _serialize(result.summary)}


@router.get("/portfolio-snapshots/{portfolio_snapshot_id}/recommendations")
def get_recommendations(
    portfolio_snapshot_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> dict[str, Any]:
    result = services.portfolio.aggregation.get_recommendations(
        _inventory_query(
            portfolio_snapshot_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            offset=0,
            limit=50,
        )
    )
    return {"envelope": _serialize(result.envelope), "summary": _serialize(result.summary)}


@router.get("/portfolio-snapshots/{portfolio_snapshot_id}/risks")
def get_risks(
    portfolio_snapshot_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> dict[str, Any]:
    result = services.portfolio.aggregation.get_risk(
        _inventory_query(
            portfolio_snapshot_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            offset=0,
            limit=50,
        )
    )
    return {"envelope": _serialize(result.envelope), "summary": _serialize(result.summary)}


@router.get("/portfolio-snapshots/{portfolio_snapshot_id}/modernization")
def get_modernization(
    portfolio_snapshot_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
    modernization_theme: Annotated[str | None, Query()] = None,
    modernization_wave: Annotated[str | None, Query()] = None,
) -> dict[str, Any]:
    result = services.portfolio.aggregation.get_modernization(
        _inventory_query(
            portfolio_snapshot_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            offset=0,
            limit=50,
            modernization_theme=modernization_theme,
            modernization_wave=modernization_wave,
        )
    )
    summary = result.summary
    candidates = list(summary.candidates)
    if modernization_theme:
        needle = modernization_theme.strip().lower()
        candidates = [item for item in candidates if item.theme.value == needle]
    if modernization_wave:
        needle = modernization_wave.strip().lower()
        candidates = [item for item in candidates if item.wave.value == needle]
    return {
        "envelope": _serialize(result.envelope),
        "summary": {
            **_serialize(summary),
            "candidates": _serialize(candidates),
        },
    }


@router.get("/portfolio-snapshots/{portfolio_snapshot_id}/coverage")
def get_coverage(
    portfolio_snapshot_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> dict[str, Any]:
    result = services.portfolio.aggregation.get_coverage(
        _inventory_query(
            portfolio_snapshot_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            offset=0,
            limit=50,
        )
    )
    return {"envelope": _serialize(result.envelope), "summary": _serialize(result.summary)}


@router.get("/portfolio-snapshots/{portfolio_snapshot_id}/repository-profiles")
def get_repository_profiles(
    portfolio_snapshot_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
    criticality: Annotated[str | None, Query()] = None,
    availability_status: Annotated[str | None, Query()] = None,
    freshness_status: Annotated[str | None, Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> dict[str, Any]:
    profiles = services.portfolio.aggregation.get_repository_profiles(
        _inventory_query(
            portfolio_snapshot_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            offset=offset,
            limit=limit,
            criticality=criticality,
            availability_status=availability_status,
            freshness_status=freshness_status,
        )
    )
    return {"items": _serialize(profiles), "total": len(profiles), "offset": offset, "limit": limit}


@router.get("/portfolio-snapshots/{portfolio_snapshot_id}/overview")
def get_overview(
    portfolio_snapshot_id: str,
    services: ServicesDep,
    organization_id: Annotated[str, Query(min_length=1)],
    workspace_id: Annotated[str, Query(min_length=1)],
) -> dict[str, Any]:
    result = services.portfolio.aggregation.get_overview(
        _inventory_query(
            portfolio_snapshot_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            offset=0,
            limit=50,
        )
    )
    return _serialize(result)


@router.post(
    "/portfolios/{portfolio_id}/archive",
    response_model=PortfolioDetailsResponse,
    include_in_schema=False,
)
def archive_portfolio(
    portfolio_id: str,
    body: BuildSnapshotRequest,
    services: ServicesDep,
) -> PortfolioDetailsResponse:
    details = services.portfolio.management.archive_portfolio(
        ArchivePortfolioCommand(
            portfolio_id=PortfolioId(portfolio_id),
            organization_id=OrganizationId(body.organization_id),
            workspace_id=WorkspaceId(body.workspace_id),
        )
    )
    return portfolio_details(details)
