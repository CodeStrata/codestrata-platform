"""Executive Intelligence application services."""

from __future__ import annotations

from codestrata_platform.application.common.errors import NotFoundError, ValidationError
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.executive_intelligence.aggregation import (
    EXECUTIVE_AGGREGATION_POLICY_VERSION,
    run_executive_aggregation,
)
from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_intelligence.errors import (
    ExecutiveIntelligenceDisabledError,
    ExecutiveIntelligenceNotFoundError,
    ExecutiveIntelligenceNotReadyError,
)
from codestrata_platform.application.executive_intelligence.models import (
    ExecutiveFindingsModel,
    ExecutiveIntelligenceDetails,
    ExecutiveIntelligenceSummary,
    ExecutiveMetricsModel,
    ExecutiveRecommendationsModel,
)
from codestrata_platform.application.executive_intelligence.policies import (
    executive_intelligence_enabled,
)
from codestrata_platform.application.executive_intelligence.queries import (
    GetExecutiveIntelligenceQuery,
    GetLatestExecutiveIntelligenceQuery,
    ListExecutiveIntelligenceQuery,
)
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
    ExecutiveProjectionKey,
)
from codestrata_platform.domain.executive_intelligence.ports import (
    ExecutiveIntelligenceRepository,
)
from codestrata_platform.domain.executive_intelligence.snapshot import (
    EXECUTIVE_SCHEMA_VERSION,
    ExecutiveIntelligenceSnapshot,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.organization.ports import OrganizationRepository
from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio.lifecycle import PortfolioSnapshotStatus
from codestrata_platform.domain.portfolio.portfolio import EngineeringPortfolio
from codestrata_platform.domain.portfolio.ports import (
    EngineeringPortfolioRepository,
    PortfolioSnapshotRepository,
)
from codestrata_platform.domain.portfolio.snapshot import PortfolioSnapshot
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.domain.workspace.ports import WorkspaceRepository


def _page(items: tuple, *, offset: int, limit: int) -> PageResult:
    bounded = max(1, min(int(limit), 500))
    start = max(0, offset)
    sliced = items[start : start + bounded]
    return PageResult(items=sliced, offset=start, limit=bounded, total=len(items))


class ExecutiveIntelligenceAggregationService:
    """Build and read Executive Intelligence projections over Portfolio Intelligence."""

    def __init__(
        self,
        *,
        executive_intelligence: ExecutiveIntelligenceRepository,
        portfolio_snapshots: PortfolioSnapshotRepository,
        portfolios: EngineeringPortfolioRepository,
        organizations: OrganizationRepository,
        workspaces: WorkspaceRepository,
    ) -> None:
        self._executive_intelligence = executive_intelligence
        self._portfolio_snapshots = portfolio_snapshots
        self._portfolios = portfolios
        self._organizations = organizations
        self._workspaces = workspaces

    def build_intelligence(
        self,
        command: BuildExecutiveIntelligenceCommand,
    ) -> ExecutiveIntelligenceDetails:
        if not executive_intelligence_enabled():
            raise ExecutiveIntelligenceDisabledError(
                "Executive Intelligence is disabled",
                reason_code="executive_intelligence_disabled",
            )
        portfolio = self._load_portfolio_owned(
            command.portfolio_id,
            command.organization_id,
            command.workspace_id,
        )
        portfolio_snapshot = self._resolve_portfolio_snapshot(command)

        projection_key = ExecutiveProjectionKey.from_parts(
            organization_id=portfolio.organization_id.value,
            workspace_id=portfolio.workspace_id.value,
            portfolio_id=portfolio.portfolio_id.value,
            portfolio_snapshot_id=portfolio_snapshot.portfolio_snapshot_id.value,
            portfolio_snapshot_version=portfolio_snapshot.version.value,
            policy_version=EXECUTIVE_AGGREGATION_POLICY_VERSION,
            schema_version=EXECUTIVE_SCHEMA_VERSION,
        )
        existing = self._executive_intelligence.find_completed_by_projection_key(
            projection_key.value
        )
        if existing is not None:
            return self._details(existing)

        version = self._executive_intelligence.latest_version_for_portfolio(
            portfolio.portfolio_id
        ) + 1
        snapshot = ExecutiveIntelligenceSnapshot.create_pending(
            organization_id=portfolio.organization_id,
            workspace_id=portfolio.workspace_id,
            portfolio_id=portfolio.portfolio_id,
            portfolio_snapshot_id=portfolio_snapshot.portfolio_snapshot_id,
            portfolio_snapshot_version=portfolio_snapshot.version.value,
            version=version,
            projection_key=projection_key,
            policy_version=EXECUTIVE_AGGREGATION_POLICY_VERSION,
        )
        snapshot.begin_aggregation()
        try:
            result = run_executive_aggregation(portfolio_snapshot)
            snapshot.complete(
                metrics=result.metrics,
                findings=result.findings,
                recommendations=result.recommendations,
                observations=result.observations,
                limitations=result.limitations,
            )
        except Exception as exc:
            snapshot.fail(str(exc)[:1000])
            self._executive_intelligence.save(snapshot)
            raise

        prior = self._executive_intelligence.latest_completed_for_portfolio(
            portfolio.portfolio_id
        )
        self._executive_intelligence.save(snapshot)
        if (
            prior is not None
            and prior.executive_intelligence_id != snapshot.executive_intelligence_id
            and prior.projection_key.value != snapshot.projection_key.value
        ):
            prior.supersede()
            self._executive_intelligence.save(prior)
        return self._details(snapshot)

    def get(self, query: GetExecutiveIntelligenceQuery) -> ExecutiveIntelligenceDetails:
        snapshot = self._load_owned(
            query.executive_intelligence_id,
            query.organization_id,
            query.workspace_id,
        )
        return self._details(snapshot)

    def get_latest(
        self,
        query: GetLatestExecutiveIntelligenceQuery,
    ) -> ExecutiveIntelligenceDetails:
        self._load_portfolio_owned(
            query.portfolio_id,
            query.organization_id,
            query.workspace_id,
        )
        snapshot = self._executive_intelligence.latest_completed_for_portfolio(
            query.portfolio_id
        )
        if snapshot is None:
            raise ExecutiveIntelligenceNotFoundError("latest")
        return self._details(snapshot)

    def list_by_portfolio(self, query: ListExecutiveIntelligenceQuery) -> PageResult:
        self._load_portfolio_owned(
            query.portfolio_id,
            query.organization_id,
            query.workspace_id,
        )
        items = self._executive_intelligence.list_by_portfolio(
            query.portfolio_id,
            limit=max(query.limit, 1) + query.offset,
        )
        summaries = tuple(self._summary(item) for item in items)
        return _page(summaries, offset=query.offset, limit=query.limit)

    def get_metrics(self, query: GetExecutiveIntelligenceQuery) -> ExecutiveMetricsModel:
        snapshot = self._load_owned(
            query.executive_intelligence_id,
            query.organization_id,
            query.workspace_id,
        )
        return ExecutiveMetricsModel(summary=self._summary(snapshot), metrics=snapshot.metrics)

    def get_findings(self, query: GetExecutiveIntelligenceQuery) -> ExecutiveFindingsModel:
        snapshot = self._load_owned(
            query.executive_intelligence_id,
            query.organization_id,
            query.workspace_id,
        )
        return ExecutiveFindingsModel(summary=self._summary(snapshot), findings=snapshot.findings)

    def get_recommendations(
        self,
        query: GetExecutiveIntelligenceQuery,
    ) -> ExecutiveRecommendationsModel:
        snapshot = self._load_owned(
            query.executive_intelligence_id,
            query.organization_id,
            query.workspace_id,
        )
        return ExecutiveRecommendationsModel(
            summary=self._summary(snapshot),
            recommendations=snapshot.recommendations,
        )

    def get_overview(self, query: GetExecutiveIntelligenceQuery) -> ExecutiveIntelligenceDetails:
        return self.get(query)

    def _resolve_portfolio_snapshot(
        self,
        command: BuildExecutiveIntelligenceCommand,
    ) -> PortfolioSnapshot:
        if command.portfolio_snapshot_id is not None:
            snapshot = self._portfolio_snapshots.get(command.portfolio_snapshot_id)
            if snapshot is None:
                raise NotFoundError(
                    f"Portfolio snapshot '{command.portfolio_snapshot_id.value}' was not found",
                    reason_code="portfolio_snapshot_not_found",
                )
        else:
            snapshot = self._portfolio_snapshots.get_latest_completed(command.portfolio_id)
            if snapshot is None:
                raise ExecutiveIntelligenceNotReadyError(
                    "Portfolio has no completed portfolio snapshot",
                    reason_code="portfolio_snapshot_not_completed",
                )
        if (
            snapshot.portfolio_id != command.portfolio_id
            or snapshot.organization_id != command.organization_id
            or snapshot.workspace_id != command.workspace_id
        ):
            raise ValidationError(
                "Portfolio snapshot does not belong to the requested portfolio/tenant",
                reason_code="portfolio_snapshot_tenant_mismatch",
            )
        if snapshot.status is not PortfolioSnapshotStatus.COMPLETED:
            raise ExecutiveIntelligenceNotReadyError(
                "Executive Intelligence requires a completed portfolio snapshot",
                reason_code="portfolio_snapshot_not_completed",
            )
        return snapshot

    def _load_portfolio_owned(
        self,
        portfolio_id: PortfolioId,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
    ) -> EngineeringPortfolio:
        portfolio = self._portfolios.get(portfolio_id)
        if portfolio is None:
            raise NotFoundError(
                f"Portfolio '{portfolio_id.value}' was not found",
                reason_code="portfolio_not_found",
            )
        if (
            portfolio.organization_id != organization_id
            or portfolio.workspace_id != workspace_id
        ):
            raise ValidationError(
                "Portfolio does not belong to the requested organization/workspace",
                reason_code="portfolio_tenant_mismatch",
            )
        return portfolio

    def _load_owned(
        self,
        executive_intelligence_id: ExecutiveIntelligenceId,
        organization_id: OrganizationId | None,
        workspace_id: WorkspaceId | None,
    ) -> ExecutiveIntelligenceSnapshot:
        snapshot = self._executive_intelligence.get(executive_intelligence_id)
        if snapshot is None:
            raise ExecutiveIntelligenceNotFoundError(executive_intelligence_id.value)
        if organization_id is not None and snapshot.organization_id != organization_id:
            raise ValidationError(
                "Executive intelligence tenant mismatch",
                reason_code="executive_intelligence_tenant_mismatch",
            )
        if workspace_id is not None and snapshot.workspace_id != workspace_id:
            raise ValidationError(
                "Executive intelligence tenant mismatch",
                reason_code="executive_intelligence_tenant_mismatch",
            )
        return snapshot

    def _summary(
        self,
        snapshot: ExecutiveIntelligenceSnapshot,
    ) -> ExecutiveIntelligenceSummary:
        return ExecutiveIntelligenceSummary(
            executive_intelligence_id=snapshot.executive_intelligence_id.value,
            organization_id=snapshot.organization_id.value,
            workspace_id=snapshot.workspace_id.value,
            portfolio_id=snapshot.portfolio_id.value,
            portfolio_snapshot_id=snapshot.portfolio_snapshot_id.value,
            portfolio_snapshot_version=snapshot.portfolio_snapshot_version,
            version=snapshot.version.value,
            status=snapshot.status,
            projection_key=snapshot.projection_key.value,
            schema_version=snapshot.schema_version,
            policy_version=snapshot.policy_version.value,
            created_at=snapshot.audit.created_at.value,
            updated_at=snapshot.audit.updated_at.value,
            completed_at=snapshot.completed_at,
            superseded_at=snapshot.superseded_at,
            failure_reason=snapshot.failure_reason,
            metric_count=len(snapshot.metrics),
            finding_count=len(snapshot.findings),
            recommendation_count=len(snapshot.recommendations),
            observation_count=len(snapshot.observations),
        )

    def _details(
        self,
        snapshot: ExecutiveIntelligenceSnapshot,
    ) -> ExecutiveIntelligenceDetails:
        return ExecutiveIntelligenceDetails(
            summary=self._summary(snapshot),
            metrics=snapshot.metrics,
            findings=snapshot.findings,
            recommendations=snapshot.recommendations,
            observations=snapshot.observations,
            limitations=snapshot.limitations,
        )
