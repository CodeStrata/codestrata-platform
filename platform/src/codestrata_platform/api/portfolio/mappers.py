"""Portfolio API mappers."""

from __future__ import annotations

from codestrata_platform.api.portfolio.dto import (
    PageResponse,
    PortfolioDetailsResponse,
    PortfolioEnvelopeResponse,
    PortfolioMembershipResponse,
    PortfolioRepositorySelectionResponse,
    PortfolioSnapshotDetailsResponse,
    PortfolioSnapshotSummaryResponse,
    PortfolioSummaryResponse,
)
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.portfolio.models import (
    PortfolioDetails,
    PortfolioSnapshotDetails,
    PortfolioSnapshotSummary,
    PortfolioSummary,
)


def portfolio_summary(item: PortfolioSummary) -> PortfolioSummaryResponse:
    return PortfolioSummaryResponse(
        portfolio_id=item.portfolio_id,
        organization_id=item.organization_id,
        workspace_id=item.workspace_id,
        name=item.name,
        description=item.description,
        status=item.status.value,
        repository_count=item.repository_count,
        created_at=item.created_at,
        updated_at=item.updated_at,
        archived_at=item.archived_at,
    )


def membership_response(membership) -> PortfolioMembershipResponse:
    return PortfolioMembershipResponse(
        membership_id=membership.membership_id,
        repository_id=membership.repository_id,
        criticality=(
            membership.criticality.value
            if hasattr(membership.criticality, "value")
            else membership.criticality
        ),
        business_capability=membership.business_capability,
        owner_reference=membership.owner_reference,
        lifecycle_status=membership.lifecycle_status,
        tags=list(membership.tags),
        added_at=membership.added_at,
        removed_at=membership.removed_at,
        active=membership.active,
    )


def portfolio_details(item: PortfolioDetails) -> PortfolioDetailsResponse:
    return PortfolioDetailsResponse(
        portfolio=portfolio_summary(item.summary),
        memberships=[membership_response(membership) for membership in item.memberships],
    )


def snapshot_summary(item: PortfolioSnapshotSummary) -> PortfolioSnapshotSummaryResponse:
    return PortfolioSnapshotSummaryResponse(
        portfolio_snapshot_id=item.portfolio_snapshot_id,
        portfolio_id=item.portfolio_id,
        organization_id=item.organization_id,
        workspace_id=item.workspace_id,
        snapshot_version=item.snapshot_version,
        status=item.status.value,
        projection_key=item.projection_key,
        aggregation_policy_version=item.aggregation_policy_version,
        repository_count=item.repository_count,
        available_repository_count=item.available_repository_count,
        unavailable_repository_count=item.unavailable_repository_count,
        created_at=item.created_at,
        completed_at=item.completed_at,
        superseded_at=item.superseded_at,
        failure_reason=item.failure_reason,
    )


def snapshot_details(item: PortfolioSnapshotDetails) -> PortfolioSnapshotDetailsResponse:
    return PortfolioSnapshotDetailsResponse(
        snapshot=snapshot_summary(item.summary),
        repository_selections=[
            PortfolioRepositorySelectionResponse(
                repository_id=selection.repository_id.value,
                availability_status=selection.availability_status.value,
                criticality=selection.criticality.value,
                assessment_id=(
                    selection.assessment_id.value if selection.assessment_id else None
                ),
                engineering_snapshot_id=selection.engineering_snapshot_id,
                engineering_snapshot_version=selection.engineering_snapshot_version,
                knowledge_graph_id=selection.knowledge_graph_id,
                knowledge_graph_version=selection.knowledge_graph_version,
                selected_at=selection.selected_at,
            )
            for selection in item.repository_selections
        ],
        envelope=PortfolioEnvelopeResponse(
            portfolio_id=item.envelope.portfolio_id,
            portfolio_snapshot_id=item.envelope.portfolio_snapshot_id,
            portfolio_snapshot_version=item.envelope.portfolio_snapshot_version,
            generated_at=item.envelope.generated_at,
            aggregation_policy_version=item.envelope.aggregation_policy_version,
            selected_repository_count=item.envelope.selected_repository_count,
            unavailable_repository_count=item.envelope.unavailable_repository_count,
            source_snapshot_references=list(item.envelope.source_snapshot_references),
        ),
    )


def page_response[T](page: PageResult[T]) -> PageResponse[T]:
    return PageResponse[T](
        items=list(page.items),
        total=page.total,
        offset=page.offset,
        limit=page.limit,
    )
