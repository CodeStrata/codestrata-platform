"""Portfolio application services."""

from __future__ import annotations

from datetime import UTC, datetime

from codestrata_platform.application.common.diagnostics import safe_failure_summary
from codestrata_platform.application.common.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.portfolio.aggregation import (
    AggregationContext,
    run_aggregation,
)
from codestrata_platform.application.portfolio.commands import (
    AddRepositoryToPortfolioCommand,
    ArchivePortfolioCommand,
    BuildPortfolioSnapshotCommand,
    CreatePortfolioCommand,
    FailPortfolioSnapshotCommand,
    RebuildPortfolioSnapshotCommand,
    RemoveRepositoryFromPortfolioCommand,
    SupersedePortfolioSnapshotCommand,
    UpdatePortfolioCommand,
)
from codestrata_platform.application.portfolio.errors import (
    PortfolioNotFoundError,
    PortfolioSnapshotNotFoundError,
)
from codestrata_platform.application.portfolio.models import (
    PortfolioAggregateEnvelope,
    PortfolioCoverageSummaryModel,
    PortfolioDetails,
    PortfolioEngineeringOverview,
    PortfolioFindingSummaryModel,
    PortfolioMembershipSummary,
    PortfolioModernizationSummaryModel,
    PortfolioRecommendationSummaryModel,
    PortfolioRepositoryProfile,
    PortfolioRiskSummaryModel,
    PortfolioSnapshotDetails,
    PortfolioSnapshotSummary,
    PortfolioSummary,
    PortfolioTechnologySummaryModel,
)
from codestrata_platform.application.portfolio.policies import (
    PORTFOLIO_AGGREGATION_POLICY_VERSION,
    AssessmentFreshnessPolicy,
    ModernizationWavePolicy,
    RecommendationPriorityPolicy,
    TechnologyStandardizationPolicy,
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
from codestrata_platform.application.portfolio.selection import (
    LatestPublishedRepositorySnapshotPolicy,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.organization.ports import OrganizationRepository
from codestrata_platform.domain.portfolio.errors import PortfolioMembershipError
from codestrata_platform.domain.portfolio.identifiers import (
    PortfolioId,
    PortfolioProjectionKey,
    PortfolioSnapshotId,
)
from codestrata_platform.domain.portfolio.lifecycle import (
    PortfolioSnapshotStatus,
    PortfolioStatus,
    RepositoryAvailabilityStatus,
)
from codestrata_platform.domain.portfolio.membership import PortfolioRepositoryReference
from codestrata_platform.domain.portfolio.portfolio import (
    DEFAULT_MAX_REPOSITORIES,
    HARD_MAX_REPOSITORIES,
    EngineeringPortfolio,
)
from codestrata_platform.domain.portfolio.ports import (
    EngineeringPortfolioRepository,
    PortfolioSnapshotRepository,
    PortfolioSourceIntelligenceRepository,
)
from codestrata_platform.domain.portfolio.snapshot import (
    PORTFOLIO_SCHEMA_VERSION,
    PortfolioSnapshot,
)
from codestrata_platform.domain.portfolio.technology import PortfolioTechnology
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.repository.ports import RepositoryRepository
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.domain.workspace.ports import WorkspaceRepository


def _page(items: tuple, *, offset: int, limit: int) -> PageResult:
    bounded = max(1, min(int(limit), 500))
    start = max(0, offset)
    sliced = items[start : start + bounded]
    return PageResult(items=sliced, offset=start, limit=bounded, total=len(items))


class PortfolioManagementService:
    """Portfolio registration and membership management."""

    def __init__(
        self,
        *,
        portfolios: EngineeringPortfolioRepository,
        organizations: OrganizationRepository,
        workspaces: WorkspaceRepository,
        repositories: RepositoryRepository,
    ) -> None:
        self._portfolios = portfolios
        self._organizations = organizations
        self._workspaces = workspaces
        self._repositories = repositories

    def create_portfolio(self, command: CreatePortfolioCommand) -> PortfolioDetails:
        self._assert_org_workspace(command.organization_id, command.workspace_id)
        max_repos = command.max_repositories or DEFAULT_MAX_REPOSITORIES
        if max_repos < 1 or max_repos > HARD_MAX_REPOSITORIES:
            raise ValidationError(
                f"max_repositories must be between 1 and {HARD_MAX_REPOSITORIES}",
                reason_code="invalid_portfolio_repository_limit",
            )
        portfolio = EngineeringPortfolio.create(
            organization_id=command.organization_id,
            workspace_id=command.workspace_id,
            name=command.name,
            description=command.description,
            max_repositories=max_repos,
        )
        self._portfolios.save(portfolio)
        return self._details(portfolio)

    def update_portfolio(self, command: UpdatePortfolioCommand) -> PortfolioDetails:
        portfolio = self._load_owned(
            command.portfolio_id,
            command.organization_id,
            command.workspace_id,
        )
        if command.name is None and command.description is None:
            raise ValidationError(
                "At least one of name or description must be provided",
                reason_code="empty_portfolio_update",
            )
        if command.name is not None:
            portfolio.rename(command.name)
        if command.description is not None:
            portfolio.update_description(command.description)
        self._portfolios.save(portfolio)
        return self._details(portfolio)

    def add_repository(self, command: AddRepositoryToPortfolioCommand) -> PortfolioDetails:
        portfolio = self._load_owned(
            command.portfolio_id,
            command.organization_id,
            command.workspace_id,
        )
        repository = self._repositories.get(command.repository_id)
        if repository is None:
            raise NotFoundError(
                f"Repository '{command.repository_id.value}' was not found",
                reason_code="repository_not_found",
            )
        if (
            repository.organization_id != command.organization_id
            or repository.workspace_id != command.workspace_id
        ):
            raise ValidationError(
                "Repository must belong to the same organization and workspace",
                reason_code="cross_tenant_membership",
            )
        try:
            portfolio.add_repository(
                PortfolioRepositoryReference(
                    organization_id=command.organization_id,
                    workspace_id=command.workspace_id,
                    repository_id=command.repository_id,
                ),
                criticality=command.criticality,
                business_capability=command.business_capability,
                owner_reference=command.owner_reference,
                lifecycle_status=command.lifecycle_status,
                tags=command.tags,
            )
        except PortfolioMembershipError as exc:
            if exc.reason_code == "duplicate_membership":
                # Idempotent: return current state.
                return self._details(portfolio)
            raise ConflictError(str(exc), reason_code=exc.reason_code) from exc
        self._portfolios.save(portfolio)
        return self._details(portfolio)

    def remove_repository(
        self,
        command: RemoveRepositoryFromPortfolioCommand,
    ) -> PortfolioDetails:
        portfolio = self._load_owned(
            command.portfolio_id,
            command.organization_id,
            command.workspace_id,
        )
        removed = portfolio.remove_repository(command.repository_id)
        if removed is None:
            raise NotFoundError(
                f"Repository '{command.repository_id.value}' is not an active portfolio member",
                reason_code="membership_not_found",
            )
        self._portfolios.save(portfolio)
        return self._details(portfolio)

    def archive_portfolio(self, command: ArchivePortfolioCommand) -> PortfolioDetails:
        portfolio = self._load_owned(
            command.portfolio_id,
            command.organization_id,
            command.workspace_id,
        )
        portfolio.archive()
        self._portfolios.save(portfolio)
        return self._details(portfolio)

    def get_portfolio(self, query: GetPortfolioQuery) -> PortfolioDetails:
        return self._details(
            self._load_owned(query.portfolio_id, query.organization_id, query.workspace_id)
        )

    def list_portfolios(self, query: ListPortfoliosQuery) -> PageResult:
        self._assert_org_workspace(query.organization_id, query.workspace_id)
        items = self._portfolios.list_by_workspace(query.workspace_id, status=query.status)
        filtered = tuple(
            item
            for item in items
            if item.organization_id == query.organization_id
        )
        summaries = tuple(self._summary(item) for item in filtered)
        return _page(summaries, offset=query.offset, limit=query.limit)

    def list_repositories(self, query: ListPortfolioRepositoriesQuery) -> PageResult:
        portfolio = self._load_owned(
            query.portfolio_id,
            query.organization_id,
            query.workspace_id,
        )
        memberships = tuple(
            self._membership_summary(item)
            for item in portfolio.active_memberships
        )
        return _page(memberships, offset=query.offset, limit=query.limit)

    def _load_owned(
        self,
        portfolio_id: PortfolioId,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
    ) -> EngineeringPortfolio:
        portfolio = self._portfolios.get(portfolio_id)
        if portfolio is None:
            raise PortfolioNotFoundError(portfolio_id.value)
        if (
            portfolio.organization_id != organization_id
            or portfolio.workspace_id != workspace_id
        ):
            raise PortfolioNotFoundError(portfolio_id.value)
        return portfolio

    def _assert_org_workspace(
        self,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
    ) -> None:
        organization = self._organizations.get(organization_id)
        if organization is None:
            raise NotFoundError(
                f"Organization '{organization_id.value}' was not found",
                reason_code="organization_not_found",
            )
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            raise NotFoundError(
                f"Workspace '{workspace_id.value}' was not found",
                reason_code="workspace_not_found",
            )
        if workspace.organization_id != organization_id:
            raise ValidationError(
                "Workspace does not belong to organization",
                reason_code="workspace_organization_mismatch",
            )

    def _summary(self, portfolio: EngineeringPortfolio) -> PortfolioSummary:
        return PortfolioSummary(
            portfolio_id=portfolio.portfolio_id.value,
            organization_id=portfolio.organization_id.value,
            workspace_id=portfolio.workspace_id.value,
            name=portfolio.name.value,
            description=portfolio.description.value,
            status=portfolio.status,
            repository_count=len(portfolio.active_memberships),
            created_at=portfolio.audit.created_at.value,
            updated_at=portfolio.audit.updated_at.value,
            archived_at=portfolio.archived_at,
        )

    def _membership_summary(self, item) -> PortfolioMembershipSummary:
        return PortfolioMembershipSummary(
            membership_id=item.membership_id.value,
            repository_id=item.repository_id.value,
            criticality=item.criticality,
            business_capability=item.business_capability,
            owner_reference=item.owner_reference,
            lifecycle_status=item.lifecycle_status,
            tags=item.tags,
            added_at=item.added_at,
            removed_at=item.removed_at,
            active=item.is_active,
        )

    def _details(self, portfolio: EngineeringPortfolio) -> PortfolioDetails:
        return PortfolioDetails(
            summary=self._summary(portfolio),
            memberships=tuple(
                self._membership_summary(item) for item in portfolio.memberships
            ),
        )


class PortfolioIntelligenceAggregationService:
    """Deterministic cross-repository portfolio aggregation."""

    def __init__(
        self,
        *,
        portfolios: EngineeringPortfolioRepository,
        snapshots: PortfolioSnapshotRepository,
        sources: PortfolioSourceIntelligenceRepository,
        organizations: OrganizationRepository,
        workspaces: WorkspaceRepository,
        auto_refresh_enabled: bool = False,
        on_snapshot_completed=None,
    ) -> None:
        self._portfolios = portfolios
        self._snapshots = snapshots
        self._sources = sources
        self._organizations = organizations
        self._workspaces = workspaces
        self._selector = LatestPublishedRepositorySnapshotPolicy(sources)
        self._auto_refresh_enabled = auto_refresh_enabled
        self._on_snapshot_completed = on_snapshot_completed
        self._standardization = TechnologyStandardizationPolicy()
        self._freshness = AssessmentFreshnessPolicy()
        self._priority = RecommendationPriorityPolicy()
        self._wave = ModernizationWavePolicy()

    def build_snapshot(self, command: BuildPortfolioSnapshotCommand) -> PortfolioSnapshotDetails:
        return self._build(command, force=command.force_rebuild)

    def rebuild_snapshot(
        self,
        command: RebuildPortfolioSnapshotCommand,
    ) -> PortfolioSnapshotDetails:
        return self._build(
            BuildPortfolioSnapshotCommand(
                portfolio_id=command.portfolio_id,
                organization_id=command.organization_id,
                workspace_id=command.workspace_id,
                aggregation_policy_version=command.aggregation_policy_version,
                force_rebuild=True,
            ),
            force=True,
        )

    def fail_snapshot(self, command: FailPortfolioSnapshotCommand) -> PortfolioSnapshotDetails:
        snapshot = self._load_snapshot_owned(
            command.portfolio_snapshot_id,
            command.organization_id,
            command.workspace_id,
        )
        snapshot.fail(command.reason)
        self._snapshots.save(snapshot)
        return self._snapshot_details(snapshot)

    def supersede_snapshot(
        self,
        command: SupersedePortfolioSnapshotCommand,
    ) -> PortfolioSnapshotDetails:
        snapshot = self._load_snapshot_owned(
            command.portfolio_snapshot_id,
            command.organization_id,
            command.workspace_id,
        )
        snapshot.supersede()
        self._snapshots.save(snapshot)
        return self._snapshot_details(snapshot)

    def get_snapshot(self, query: GetPortfolioSnapshotQuery) -> PortfolioSnapshotDetails:
        snapshot = self._snapshots.get(query.portfolio_snapshot_id)
        if snapshot is None:
            raise PortfolioSnapshotNotFoundError(query.portfolio_snapshot_id.value)
        if (
            snapshot.organization_id != query.organization_id
            or snapshot.workspace_id != query.workspace_id
        ):
            raise PortfolioSnapshotNotFoundError(query.portfolio_snapshot_id.value)
        return self._snapshot_details(snapshot)

    def get_latest_snapshot(
        self,
        query: GetLatestPortfolioSnapshotQuery,
    ) -> PortfolioSnapshotDetails:
        self._load_portfolio_owned(
            query.portfolio_id,
            query.organization_id,
            query.workspace_id,
        )
        snapshot = self._snapshots.get_latest_completed(query.portfolio_id)
        if snapshot is None:
            raise PortfolioSnapshotNotFoundError("latest")
        return self._snapshot_details(snapshot)

    def list_snapshots(self, query: ListPortfolioSnapshotsQuery) -> PageResult:
        self._load_portfolio_owned(
            query.portfolio_id,
            query.organization_id,
            query.workspace_id,
        )
        bounded = max(1, min(int(query.limit), 500))
        start = max(0, query.offset)
        total = self._snapshots.count_by_portfolio(query.portfolio_id)
        items = self._snapshots.list_by_portfolio(
            query.portfolio_id,
            offset=start,
            limit=bounded,
        )
        summaries = tuple(self._snapshot_summary(item) for item in items)
        return PageResult(items=summaries, offset=start, limit=bounded, total=total)

    def get_technologies(self, query: PortfolioInventoryQuery) -> PortfolioTechnologySummaryModel:
        snapshot = self._require_completed(query)
        items = list(snapshot.technology_inventory)
        if query.technology:
            needle = query.technology.strip().lower()
            items = [
                item
                for item in items
                if isinstance(item, PortfolioTechnology)
                and needle in item.canonical_key.lower()
            ]
        if query.framework:
            needle = query.framework.strip().lower()
            items = [
                item
                for item in items
                if isinstance(item, PortfolioTechnology)
                and (item.framework or "").lower() == needle
            ]
        page = _page(tuple(items), offset=query.offset, limit=query.limit)
        return PortfolioTechnologySummaryModel(
            envelope=self._envelope(snapshot),
            items=page.items,  # type: ignore[arg-type]
            total=page.total,
        )

    def get_findings(self, query: PortfolioInventoryQuery) -> PortfolioFindingSummaryModel:
        snapshot = self._require_completed(query)
        summary = snapshot.finding_inventory[0] if snapshot.finding_inventory else None
        if summary is None:
            raise ValidationError("Finding inventory missing", reason_code="missing_findings")
        return PortfolioFindingSummaryModel(
            envelope=self._envelope(snapshot),
            summary=summary,  # type: ignore[arg-type]
        )

    def get_recommendations(
        self,
        query: PortfolioInventoryQuery,
    ) -> PortfolioRecommendationSummaryModel:
        snapshot = self._require_completed(query)
        summary = (
            snapshot.recommendation_inventory[0] if snapshot.recommendation_inventory else None
        )
        if summary is None:
            raise ValidationError(
                "Recommendation inventory missing",
                reason_code="missing_recommendations",
            )
        return PortfolioRecommendationSummaryModel(
            envelope=self._envelope(snapshot),
            summary=summary,  # type: ignore[arg-type]
        )

    def get_risk(self, query: PortfolioInventoryQuery) -> PortfolioRiskSummaryModel:
        snapshot = self._require_completed(query)
        if snapshot.risk_summary is None:
            raise ValidationError("Risk summary missing", reason_code="missing_risk")
        return PortfolioRiskSummaryModel(
            envelope=self._envelope(snapshot),
            summary=snapshot.risk_summary,  # type: ignore[arg-type]
        )

    def get_modernization(
        self,
        query: PortfolioInventoryQuery,
    ) -> PortfolioModernizationSummaryModel:
        snapshot = self._require_completed(query)
        if snapshot.modernization_summary is None:
            raise ValidationError(
                "Modernization summary missing",
                reason_code="missing_modernization",
            )
        return PortfolioModernizationSummaryModel(
            envelope=self._envelope(snapshot),
            summary=snapshot.modernization_summary,  # type: ignore[arg-type]
        )

    def get_coverage(self, query: PortfolioInventoryQuery) -> PortfolioCoverageSummaryModel:
        snapshot = self._require_completed(query)
        if snapshot.coverage_summary is None:
            raise ValidationError("Coverage summary missing", reason_code="missing_coverage")
        return PortfolioCoverageSummaryModel(
            envelope=self._envelope(snapshot),
            summary=snapshot.coverage_summary,  # type: ignore[arg-type]
        )

    def get_repository_profiles(
        self,
        query: PortfolioInventoryQuery,
    ) -> tuple[PortfolioRepositoryProfile, ...]:
        overview = self.get_overview(query)
        profiles = overview.repository_profiles
        if query.criticality:
            profiles = tuple(
                item
                for item in profiles
                if item.criticality.value == query.criticality.strip().lower()
            )
        if query.availability_status:
            profiles = tuple(
                item
                for item in profiles
                if item.availability_status == query.availability_status.strip().lower()
            )
        if query.freshness_status:
            profiles = tuple(
                item
                for item in profiles
                if (item.freshness_status or "") == query.freshness_status.strip().lower()
            )
        page = _page(profiles, offset=query.offset, limit=query.limit)
        return page.items  # type: ignore[return-value]

    def get_overview(self, query: PortfolioInventoryQuery) -> PortfolioEngineeringOverview:
        snapshot = self._require_completed(query)
        findings = snapshot.finding_inventory[0]
        recommendations = snapshot.recommendation_inventory[0]
        risk = snapshot.risk_summary
        modernization = snapshot.modernization_summary
        coverage = snapshot.coverage_summary
        dependencies = (
            snapshot.dependency_signals[0]
            if snapshot.dependency_signals
            else None
        )
        if dependencies is None:
            from codestrata_platform.domain.portfolio.taxonomy import SharedDependencySummary

            dependencies = SharedDependencySummary(
                signals=(),
                explicit_dependency_count=0,
                shared_exposure_count=0,
            )
        risk_by_repo = {
            profile.repository_id.value: profile
            for profile in risk.repository_profiles  # type: ignore[union-attr]
        }
        coverage_by_repo = {
            status.repository_id.value: status
            for status in coverage.repository_statuses  # type: ignore[union-attr]
        }
        tech_by_repo: dict[str, int] = {}
        for tech in snapshot.technology_inventory:
            if not isinstance(tech, PortfolioTechnology):
                continue
            for repo in tech.repository_references:
                tech_by_repo[repo.value] = tech_by_repo.get(repo.value, 0) + 1

        profiles: list[PortfolioRepositoryProfile] = []
        for selection in snapshot.repository_selections:
            risk_profile = risk_by_repo.get(selection.repository_id.value)
            cov = coverage_by_repo.get(selection.repository_id.value)
            profiles.append(
                PortfolioRepositoryProfile(
                    repository_id=selection.repository_id.value,
                    criticality=selection.criticality,
                    availability_status=selection.availability_status.value,
                    engineering_snapshot_id=selection.engineering_snapshot_id,
                    engineering_snapshot_version=selection.engineering_snapshot_version,
                    knowledge_graph_id=selection.knowledge_graph_id,
                    risk_score=risk_profile.score if risk_profile else None,
                    risk_band=risk_profile.band.value if risk_profile else None,
                    finding_count=risk_profile.finding_count if risk_profile else 0,
                    high_critical_count=risk_profile.high_critical_count if risk_profile else 0,
                    technology_count=tech_by_repo.get(selection.repository_id.value, 0),
                    recommendation_count=0,
                    freshness_status=cov.freshness_status.value if cov else None,
                )
            )
        return PortfolioEngineeringOverview(
            envelope=self._envelope(snapshot),
            technologies=tuple(
                item
                for item in snapshot.technology_inventory
                if isinstance(item, PortfolioTechnology)
            ),
            findings=findings,  # type: ignore[arg-type]
            recommendations=recommendations,  # type: ignore[arg-type]
            risk=risk,  # type: ignore[arg-type]
            modernization=modernization,  # type: ignore[arg-type]
            coverage=coverage,  # type: ignore[arg-type]
            dependencies=dependencies,  # type: ignore[arg-type]
            repository_profiles=tuple(
                sorted(profiles, key=lambda item: item.repository_id)
            ),
        )

    def mark_stale_for_repository(self, repository_id: RepositoryId) -> tuple[PortfolioId, ...]:
        """Optionally mark portfolios as refresh candidates when auto-refresh is enabled."""

        if not self._auto_refresh_enabled:
            return ()
        affected = self._portfolios.list_containing_repository(repository_id)
        return tuple(item.portfolio_id for item in affected)

    def _build(
        self,
        command: BuildPortfolioSnapshotCommand,
        *,
        force: bool,
    ) -> PortfolioSnapshotDetails:
        portfolio = self._load_portfolio_owned(
            command.portfolio_id,
            command.organization_id,
            command.workspace_id,
        )
        if portfolio.status is PortfolioStatus.ARCHIVED:
            raise ValidationError(
                "Archived portfolios cannot accept new snapshots",
                reason_code="portfolio_archived",
            )

        policy_version = (
            command.aggregation_policy_version or PORTFOLIO_AGGREGATION_POLICY_VERSION
        )
        memberships = portfolio.active_memberships
        selections, intelligence_loaded = self._selector.select_with_sources(memberships)
        intelligence: dict[str, object] = dict(intelligence_loaded)

        selected_snaps = tuple(
            (
                item.engineering_snapshot_id or "",
                item.engineering_snapshot_version or 0,
            )
            for item in selections
            if item.availability_status is RepositoryAvailabilityStatus.AVAILABLE
            and item.engineering_snapshot_id
        )
        selected_graphs = tuple(
            (
                item.knowledge_graph_id or "",
                item.knowledge_graph_version or 0,
            )
            for item in selections
            if item.knowledge_graph_id
        )
        projection_key = PortfolioProjectionKey.from_parts(
            portfolio_id=portfolio.portfolio_id.value,
            membership_repository_ids=tuple(
                item.repository_id.value for item in memberships
            ),
            selected_snapshots=selected_snaps,
            selected_graphs=selected_graphs,
            aggregation_policy_version=policy_version,
            portfolio_schema_version=PORTFOLIO_SCHEMA_VERSION,
        )

        existing = self._snapshots.find_completed_by_projection_key(projection_key.value)
        if existing is not None:
            # Same projection is idempotent; force rebuild cannot diverge deterministically.
            return self._snapshot_details(existing)

        # Free any FAILED row that still occupies this unique projection key.
        for prior_failed in self._snapshots.list_by_portfolio(
            portfolio.portfolio_id,
            status=PortfolioSnapshotStatus.FAILED,
            limit=100,
        ):
            if prior_failed.projection_key.value == projection_key.value:
                prior_failed.projection_key = PortfolioProjectionKey(
                    f"{projection_key.value}:f{prior_failed.version.value}"[:128]
                )
                self._snapshots.save(prior_failed)
                break

        version = self._snapshots.latest_version_for_portfolio(portfolio.portfolio_id) + 1
        snapshot = PortfolioSnapshot.create_pending(
            portfolio_id=portfolio.portfolio_id,
            organization_id=portfolio.organization_id,
            workspace_id=portfolio.workspace_id,
            version=version,
            projection_key=projection_key,
            aggregation_policy_version=policy_version,
        )
        snapshot.begin_aggregation()
        for selection in selections:
            snapshot.attach_repository_snapshot(selection)

        try:
            # Validate selected snapshot ownership
            for selection in selections:
                if selection.availability_status is RepositoryAvailabilityStatus.UNAVAILABLE:
                    continue
                intel = intelligence.get(selection.repository_id.value)
                if intel is None:
                    raise ValidationError(
                        "Selected repository intelligence missing",
                        reason_code="missing_repository_intelligence",
                    )
                snap = intel.engineering_snapshot  # type: ignore[attr-defined]
                if (
                    snap.organization_id != portfolio.organization_id
                    or snap.workspace_id != portfolio.workspace_id
                    or snap.repository_id != selection.repository_id
                ):
                    raise ValidationError(
                        "Selected snapshot ownership mismatch",
                        reason_code="snapshot_ownership_mismatch",
                    )

            context = AggregationContext(
                portfolio_snapshot_id=snapshot.portfolio_snapshot_id.value,
                memberships=memberships,
                selections=selections,
                intelligence=intelligence,  # type: ignore[arg-type]
                evaluated_at=datetime.now(UTC),
                standardization=self._standardization,
                freshness=self._freshness,
                priority=self._priority,
                wave=self._wave,
                policy_version=policy_version,
            )
            aggregates = run_aggregation(context)
            snapshot.attach_technology_inventory(aggregates["technologies"])  # type: ignore[arg-type]
            snapshot.attach_finding_inventory((aggregates["findings"],))
            snapshot.attach_recommendation_inventory((aggregates["recommendations"],))
            snapshot.attach_risk_summary(aggregates["risk"])
            snapshot.attach_modernization_summary(aggregates["modernization"])
            snapshot.attach_coverage_summary(aggregates["coverage"])
            snapshot.attach_dependency_signals((aggregates["dependencies"],))
            snapshot.complete()
        except Exception as exc:
            snapshot.fail(safe_failure_summary(exc, limit=2000))
            # Free the unique projection_key so deterministic retries can rebuild.
            snapshot.projection_key = PortfolioProjectionKey(
                f"{projection_key.value}:f{snapshot.version.value}"[:128]
            )
            self._snapshots.save(snapshot)
            raise

        prior = self._snapshots.get_latest_completed(portfolio.portfolio_id)
        self._snapshots.save(snapshot)
        if (
            prior is not None
            and prior.portfolio_snapshot_id != snapshot.portfolio_snapshot_id
            and prior.status is PortfolioSnapshotStatus.COMPLETED
            and prior.projection_key.value != snapshot.projection_key.value
        ):
            prior.supersede()
            self._snapshots.save(prior)
        if self._on_snapshot_completed is not None:
            try:
                self._on_snapshot_completed(snapshot.portfolio_snapshot_id)
            except Exception:
                # Portfolio retrieval auto-index failures must not invalidate snapshot.
                pass
        return self._snapshot_details(snapshot)

    def _require_completed(self, query: PortfolioInventoryQuery) -> PortfolioSnapshot:
        snapshot = self._snapshots.get(query.portfolio_snapshot_id)
        if snapshot is None:
            raise PortfolioSnapshotNotFoundError(query.portfolio_snapshot_id.value)
        if (
            snapshot.organization_id != query.organization_id
            or snapshot.workspace_id != query.workspace_id
        ):
            raise PortfolioSnapshotNotFoundError(query.portfolio_snapshot_id.value)
        if snapshot.status is not PortfolioSnapshotStatus.COMPLETED:
            raise ValidationError(
                "Portfolio snapshot is not completed",
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
            raise PortfolioNotFoundError(portfolio_id.value)
        if (
            portfolio.organization_id != organization_id
            or portfolio.workspace_id != workspace_id
        ):
            raise PortfolioNotFoundError(portfolio_id.value)
        return portfolio

    def _load_snapshot_owned(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
    ) -> PortfolioSnapshot:
        snapshot = self._snapshots.get(portfolio_snapshot_id)
        if snapshot is None:
            raise PortfolioSnapshotNotFoundError(portfolio_snapshot_id.value)
        if (
            snapshot.organization_id != organization_id
            or snapshot.workspace_id != workspace_id
        ):
            raise PortfolioSnapshotNotFoundError(portfolio_snapshot_id.value)
        return snapshot

    def _envelope(self, snapshot: PortfolioSnapshot) -> PortfolioAggregateEnvelope:
        sources = tuple(
            sorted(
                {
                    item.engineering_snapshot_id
                    for item in snapshot.repository_selections
                    if item.engineering_snapshot_id
                }
            )
        )
        return PortfolioAggregateEnvelope(
            portfolio_id=snapshot.portfolio_id.value,
            portfolio_snapshot_id=snapshot.portfolio_snapshot_id.value,
            portfolio_snapshot_version=snapshot.version.value,
            generated_at=snapshot.completed_at or snapshot.audit.updated_at.value,
            aggregation_policy_version=snapshot.aggregation_policy_version.value,
            selected_repository_count=snapshot.available_repository_count,
            unavailable_repository_count=snapshot.unavailable_repository_count,
            source_snapshot_references=sources,
        )

    def _snapshot_summary(self, snapshot: PortfolioSnapshot) -> PortfolioSnapshotSummary:
        return PortfolioSnapshotSummary(
            portfolio_snapshot_id=snapshot.portfolio_snapshot_id.value,
            portfolio_id=snapshot.portfolio_id.value,
            organization_id=snapshot.organization_id.value,
            workspace_id=snapshot.workspace_id.value,
            snapshot_version=snapshot.version.value,
            status=snapshot.status,
            projection_key=snapshot.projection_key.value,
            aggregation_policy_version=snapshot.aggregation_policy_version.value,
            repository_count=snapshot.repository_count,
            available_repository_count=snapshot.available_repository_count,
            unavailable_repository_count=snapshot.unavailable_repository_count,
            created_at=snapshot.audit.created_at.value,
            completed_at=snapshot.completed_at,
            superseded_at=snapshot.superseded_at,
            failure_reason=snapshot.failure_reason,
        )

    def _snapshot_details(self, snapshot: PortfolioSnapshot) -> PortfolioSnapshotDetails:
        return PortfolioSnapshotDetails(
            summary=self._snapshot_summary(snapshot),
            repository_selections=snapshot.repository_selections,
            envelope=self._envelope(snapshot),
        )


class PortfolioServiceFacade:
    """Facade exposing management + aggregation for API/DI wiring."""

    def __init__(
        self,
        management: PortfolioManagementService,
        aggregation: PortfolioIntelligenceAggregationService,
    ) -> None:
        self.management = management
        self.aggregation = aggregation

    def summarize_portfolio(
        self,
        *,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId | None = None,
    ) -> object:
        if workspace_id is None:
            raise ValidationError(
                "workspace_id is required for portfolio summary",
                reason_code="workspace_required",
            )
        portfolios = self.management.list_portfolios(
            ListPortfoliosQuery(
                organization_id=organization_id,
                workspace_id=workspace_id,
                status=PortfolioStatus.ACTIVE,
            )
        )
        return portfolios
