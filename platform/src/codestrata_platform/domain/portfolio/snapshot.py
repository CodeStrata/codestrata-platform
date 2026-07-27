"""PortfolioSnapshot aggregate and selection records."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvariantViolationError,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.errors import PortfolioSnapshotError
from codestrata_platform.domain.portfolio.identifiers import (
    PortfolioId,
    PortfolioPolicyVersion,
    PortfolioProjectionKey,
    PortfolioSnapshotId,
    PortfolioSnapshotVersion,
)
from codestrata_platform.domain.portfolio.lifecycle import (
    PortfolioSnapshotStatus,
    RepositoryAvailabilityStatus,
    RepositoryCriticality,
)
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.workspace.ids import WorkspaceId

PORTFOLIO_SCHEMA_VERSION = "portfolio-schema-v1"
DEFAULT_AGGREGATION_POLICY_VERSION = "portfolio-aggregation-v1"


@dataclass(frozen=True, slots=True)
class PortfolioRepositorySnapshotSelection:
    """Frozen repository intelligence selection for one portfolio snapshot."""

    repository_id: RepositoryId
    availability_status: RepositoryAvailabilityStatus
    selected_at: datetime
    criticality: RepositoryCriticality = RepositoryCriticality.UNSPECIFIED
    assessment_id: AssessmentId | None = None
    engineering_snapshot_id: str | None = None
    engineering_snapshot_version: int | None = None
    knowledge_graph_id: str | None = None
    knowledge_graph_version: int | None = None
    graph_intelligence_policy_version: str | None = None


@dataclass(slots=True)
class PortfolioSnapshot:
    """Deterministic aggregate projection across selected repository snapshots."""

    portfolio_snapshot_id: PortfolioSnapshotId
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    version: PortfolioSnapshotVersion
    status: PortfolioSnapshotStatus
    projection_key: PortfolioProjectionKey
    portfolio_schema_version: str
    aggregation_policy_version: PortfolioPolicyVersion
    repository_selections: tuple[PortfolioRepositorySnapshotSelection, ...]
    audit: AuditInfo
    completed_at: datetime | None = None
    superseded_at: datetime | None = None
    failure_reason: str | None = None
    technology_inventory: tuple[object, ...] = ()
    finding_inventory: tuple[object, ...] = ()
    recommendation_inventory: tuple[object, ...] = ()
    risk_summary: object | None = None
    modernization_summary: object | None = None
    coverage_summary: object | None = None
    dependency_signals: tuple[object, ...] = ()
    _version: int = field(default=0, repr=False)

    @classmethod
    def create_pending(
        cls,
        *,
        portfolio_id: PortfolioId,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        version: int,
        projection_key: PortfolioProjectionKey,
        aggregation_policy_version: str = DEFAULT_AGGREGATION_POLICY_VERSION,
        portfolio_schema_version: str = PORTFOLIO_SCHEMA_VERSION,
        portfolio_snapshot_id: PortfolioSnapshotId | None = None,
        audit: AuditInfo | None = None,
    ) -> PortfolioSnapshot:
        return cls(
            portfolio_snapshot_id=portfolio_snapshot_id or PortfolioSnapshotId.generate(),
            portfolio_id=portfolio_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            version=PortfolioSnapshotVersion(version),
            status=PortfolioSnapshotStatus.PENDING,
            projection_key=projection_key,
            portfolio_schema_version=portfolio_schema_version,
            aggregation_policy_version=PortfolioPolicyVersion(aggregation_policy_version),
            repository_selections=(),
            audit=audit or AuditInfo.create(),
        )

    @property
    def repository_count(self) -> int:
        return len(self.repository_selections)

    @property
    def available_repository_count(self) -> int:
        return sum(
            1
            for item in self.repository_selections
            if item.availability_status is RepositoryAvailabilityStatus.AVAILABLE
        )

    @property
    def unavailable_repository_count(self) -> int:
        return self.repository_count - self.available_repository_count

    def begin_aggregation(self) -> None:
        self._ensure_mutable()
        if self.status not in {
            PortfolioSnapshotStatus.PENDING,
            PortfolioSnapshotStatus.AGGREGATING,
        }:
            raise InvalidStateTransitionError(
                "Only pending snapshots may begin aggregation",
                reason_code="invalid_begin_aggregation",
            )
        self.status = PortfolioSnapshotStatus.AGGREGATING
        self._touch()

    def attach_repository_snapshot(
        self,
        selection: PortfolioRepositorySnapshotSelection,
    ) -> None:
        self._ensure_mutable()
        if any(
            item.repository_id == selection.repository_id for item in self.repository_selections
        ):
            raise PortfolioSnapshotError(
                "Repository already selected for this portfolio snapshot",
                reason_code="duplicate_repository_selection",
            )
        self.repository_selections = (*self.repository_selections, selection)
        self._touch()

    def attach_technology_inventory(self, items: tuple[object, ...]) -> None:
        self._ensure_aggregating()
        self.technology_inventory = items
        self._touch()

    def attach_finding_inventory(self, items: tuple[object, ...]) -> None:
        self._ensure_aggregating()
        self.finding_inventory = items
        self._touch()

    def attach_recommendation_inventory(self, items: tuple[object, ...]) -> None:
        self._ensure_aggregating()
        self.recommendation_inventory = items
        self._touch()

    def attach_risk_summary(self, summary: object) -> None:
        self._ensure_aggregating()
        self.risk_summary = summary
        self._touch()

    def attach_modernization_summary(self, summary: object) -> None:
        self._ensure_aggregating()
        self.modernization_summary = summary
        self._touch()

    def attach_coverage_summary(self, summary: object) -> None:
        self._ensure_aggregating()
        self.coverage_summary = summary
        self._touch()

    def attach_dependency_signals(self, signals: tuple[object, ...]) -> None:
        self._ensure_aggregating()
        self.dependency_signals = signals
        self._touch()

    def complete(self) -> None:
        self._ensure_aggregating()
        if (
            self.risk_summary is None
            or self.modernization_summary is None
            or self.coverage_summary is None
        ):
            raise InvariantViolationError(
                "Portfolio snapshot aggregates are incomplete",
                reason_code="incomplete_portfolio_aggregates",
            )
        self.status = PortfolioSnapshotStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self._touch()

    def fail(self, reason: str) -> None:
        self._ensure_mutable()
        compact = reason.strip()
        if not compact:
            raise PortfolioSnapshotError(
                "Failure reason must be non-blank",
                reason_code="empty_failure_reason",
            )
        self.status = PortfolioSnapshotStatus.FAILED
        self.failure_reason = compact[:2000]
        self._touch()

    def supersede(self) -> None:
        if self.status is not PortfolioSnapshotStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Only completed snapshots may be superseded",
                reason_code="invalid_supersede",
            )
        self.status = PortfolioSnapshotStatus.SUPERSEDED
        self.superseded_at = datetime.now(UTC)
        self._touch()

    def archive(self) -> None:
        if self.status in {
            PortfolioSnapshotStatus.FAILED,
            PortfolioSnapshotStatus.SUPERSEDED,
            PortfolioSnapshotStatus.ARCHIVED,
        }:
            self.status = PortfolioSnapshotStatus.ARCHIVED
            self._touch()
            return
        if self.status is not PortfolioSnapshotStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Only completed, failed, or superseded snapshots may be archived",
                reason_code="invalid_archive",
            )
        self.status = PortfolioSnapshotStatus.ARCHIVED
        self._touch()

    def _ensure_mutable(self) -> None:
        if self.status is PortfolioSnapshotStatus.COMPLETED:
            raise PortfolioSnapshotError(
                "Completed portfolio snapshots are immutable",
                reason_code="completed_snapshot_immutable",
            )
        if self.status in {
            PortfolioSnapshotStatus.SUPERSEDED,
            PortfolioSnapshotStatus.ARCHIVED,
            PortfolioSnapshotStatus.FAILED,
        }:
            raise PortfolioSnapshotError(
                "Terminal portfolio snapshots cannot be mutated",
                reason_code="terminal_snapshot_immutable",
            )

    def _ensure_aggregating(self) -> None:
        self._ensure_mutable()
        if self.status is not PortfolioSnapshotStatus.AGGREGATING:
            raise InvalidStateTransitionError(
                "Aggregates may only be attached while aggregating",
                reason_code="not_aggregating",
            )

    def _touch(self) -> None:
        self.audit = self.audit.touch()
        self._version += 1

    def snapshot(self) -> PortfolioSnapshot:
        return replace(
            self,
            repository_selections=self.repository_selections,
            technology_inventory=self.technology_inventory,
            finding_inventory=self.finding_inventory,
            recommendation_inventory=self.recommendation_inventory,
            dependency_signals=self.dependency_signals,
            audit=self.audit,
        )
