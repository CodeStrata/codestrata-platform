"""ExecutiveIntelligenceSnapshot aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.errors import InvalidStateTransitionError, InvalidValueError
from codestrata_platform.domain.executive_intelligence.errors import (
    ExecutiveIntelligenceInvariantError,
)
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
    ExecutiveIntelligenceVersion,
    ExecutivePolicyVersion,
    ExecutiveProjectionKey,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveIntelligenceStatus,
)
from codestrata_platform.domain.executive_intelligence.models import (
    ExecutiveFinding,
    ExecutiveMetric,
    ExecutiveRecommendation,
    StrategicObservation,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.workspace.ids import WorkspaceId

EXECUTIVE_SCHEMA_VERSION = "executive-schema-v1"
DEFAULT_EXECUTIVE_POLICY_VERSION = "executive-aggregation-v1"


@dataclass(slots=True)
class ExecutiveIntelligenceSnapshot:
    """Deterministic leadership projection over one completed Portfolio Snapshot."""

    executive_intelligence_id: ExecutiveIntelligenceId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    portfolio_id: PortfolioId
    portfolio_snapshot_id: PortfolioSnapshotId
    portfolio_snapshot_version: int
    version: ExecutiveIntelligenceVersion
    status: ExecutiveIntelligenceStatus
    projection_key: ExecutiveProjectionKey
    schema_version: str
    policy_version: ExecutivePolicyVersion
    metrics: tuple[ExecutiveMetric, ...]
    findings: tuple[ExecutiveFinding, ...]
    recommendations: tuple[ExecutiveRecommendation, ...]
    observations: tuple[StrategicObservation, ...]
    limitations: tuple[str, ...]
    audit: AuditInfo
    completed_at: datetime | None = None
    superseded_at: datetime | None = None
    failure_reason: str | None = None
    _version: int = field(default=0, repr=False)

    @classmethod
    def create_pending(
        cls,
        *,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        portfolio_id: PortfolioId,
        portfolio_snapshot_id: PortfolioSnapshotId,
        portfolio_snapshot_version: int,
        version: int,
        projection_key: ExecutiveProjectionKey,
        policy_version: str = DEFAULT_EXECUTIVE_POLICY_VERSION,
        schema_version: str = EXECUTIVE_SCHEMA_VERSION,
        executive_intelligence_id: ExecutiveIntelligenceId | None = None,
    ) -> ExecutiveIntelligenceSnapshot:
        if portfolio_snapshot_version < 1:
            raise InvalidValueError(
                "portfolio_snapshot_version must be >= 1",
                reason_code="invalid_portfolio_snapshot_version",
            )
        return cls(
            executive_intelligence_id=(
                executive_intelligence_id or ExecutiveIntelligenceId.generate()
            ),
            organization_id=organization_id,
            workspace_id=workspace_id,
            portfolio_id=portfolio_id,
            portfolio_snapshot_id=portfolio_snapshot_id,
            portfolio_snapshot_version=portfolio_snapshot_version,
            version=ExecutiveIntelligenceVersion(version),
            status=ExecutiveIntelligenceStatus.PENDING,
            projection_key=projection_key,
            schema_version=schema_version,
            policy_version=ExecutivePolicyVersion(policy_version),
            metrics=(),
            findings=(),
            recommendations=(),
            observations=(),
            limitations=(),
            audit=AuditInfo.create(),
        )

    def begin_aggregation(self) -> None:
        self._ensure_mutable()
        if self.status not in {
            ExecutiveIntelligenceStatus.PENDING,
            ExecutiveIntelligenceStatus.AGGREGATING,
        }:
            raise InvalidStateTransitionError(
                "Only pending executive intelligence may begin aggregation",
                reason_code="invalid_begin_executive_aggregation",
            )
        self.status = ExecutiveIntelligenceStatus.AGGREGATING
        self._touch()

    def complete(
        self,
        *,
        metrics: tuple[ExecutiveMetric, ...],
        findings: tuple[ExecutiveFinding, ...],
        recommendations: tuple[ExecutiveRecommendation, ...],
        observations: tuple[StrategicObservation, ...],
        limitations: tuple[str, ...] = (),
    ) -> None:
        self._ensure_mutable()
        if self.status is not ExecutiveIntelligenceStatus.AGGREGATING:
            raise InvalidStateTransitionError(
                "Executive intelligence must be aggregating before complete",
                reason_code="invalid_complete_executive_intelligence",
            )
        if not metrics:
            raise ExecutiveIntelligenceInvariantError(
                "Completed executive intelligence requires metrics",
                reason_code="missing_executive_metrics",
            )
        keys = [item.key for item in metrics]
        if len(keys) != len(set(keys)):
            raise ExecutiveIntelligenceInvariantError(
                "Executive metrics must be unique by key",
                reason_code="duplicate_executive_metric_key",
            )
        self.metrics = metrics
        self.findings = findings
        self.recommendations = recommendations
        self.observations = observations
        self.limitations = tuple(item.strip() for item in limitations if item.strip())
        self.status = ExecutiveIntelligenceStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.failure_reason = None
        self._touch()

    def fail(self, reason: str) -> None:
        self._ensure_mutable()
        compact = reason.strip()
        if not compact:
            raise InvalidValueError(
                "failure reason must be non-blank",
                reason_code="empty_executive_failure_reason",
            )
        self.status = ExecutiveIntelligenceStatus.FAILED
        self.failure_reason = compact[:1000]
        self.metrics = ()
        self.findings = ()
        self.recommendations = ()
        self.observations = ()
        self._touch()

    def supersede(self) -> None:
        if self.status is not ExecutiveIntelligenceStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Only completed executive intelligence may be superseded",
                reason_code="invalid_supersede_executive_intelligence",
            )
        self.status = ExecutiveIntelligenceStatus.SUPERSEDED
        self.superseded_at = datetime.now(UTC)
        self._touch()

    def snapshot(self) -> ExecutiveIntelligenceSnapshot:
        return replace(self)

    def _ensure_mutable(self) -> None:
        if self.status in {
            ExecutiveIntelligenceStatus.COMPLETED,
            ExecutiveIntelligenceStatus.FAILED,
            ExecutiveIntelligenceStatus.SUPERSEDED,
        }:
            raise InvalidStateTransitionError(
                f"Executive intelligence in status {self.status.value} is immutable",
                reason_code="executive_intelligence_immutable",
            )

    def _touch(self) -> None:
        self.audit = self.audit.touch()
        self._version += 1
