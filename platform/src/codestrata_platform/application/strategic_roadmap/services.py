"""Strategic Portfolio Roadmap application services (on-read projection)."""

from __future__ import annotations

from codestrata_platform.application.executive_intelligence.models import (
    ExecutiveIntelligenceDetails,
)
from codestrata_platform.application.executive_intelligence.queries import (
    GetExecutiveIntelligenceQuery,
    GetLatestExecutiveIntelligenceQuery,
)
from codestrata_platform.application.executive_intelligence.services import (
    ExecutiveIntelligenceAggregationService,
)
from codestrata_platform.application.strategic_roadmap.builder import (
    StrategicRoadmapBuilder,
)
from codestrata_platform.application.strategic_roadmap.errors import (
    StrategicRoadmapDisabledError,
    StrategicRoadmapNotFoundError,
    StrategicRoadmapNotReadyError,
)
from codestrata_platform.application.strategic_roadmap.models import StrategicRoadmapModel
from codestrata_platform.application.strategic_roadmap.policies import (
    strategic_roadmap_enabled,
)
from codestrata_platform.application.strategic_roadmap.queries import (
    GetLatestStrategicRoadmapQuery,
    GetStrategicRoadmapByPortfolioSnapshotQuery,
    GetStrategicRoadmapQuery,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveIntelligenceStatus,
)
from codestrata_platform.domain.executive_intelligence.ports import (
    ExecutiveIntelligenceRepository,
)


class StrategicRoadmapService:
    """Load completed Executive Intelligence and project roadmap models on read."""

    def __init__(
        self,
        *,
        executive_intelligence: ExecutiveIntelligenceAggregationService,
        executive_intelligence_repository: ExecutiveIntelligenceRepository,
        builder: StrategicRoadmapBuilder | None = None,
    ) -> None:
        self._executive_intelligence = executive_intelligence
        self._executive_intelligence_repository = executive_intelligence_repository
        self._builder = builder or StrategicRoadmapBuilder()

    def get(self, query: GetStrategicRoadmapQuery) -> StrategicRoadmapModel:
        self._ensure_enabled()
        details = self._executive_intelligence.get(
            GetExecutiveIntelligenceQuery(
                executive_intelligence_id=query.executive_intelligence_id,
                organization_id=query.organization_id,
                workspace_id=query.workspace_id,
            )
        )
        return self._project(details)

    def get_latest(self, query: GetLatestStrategicRoadmapQuery) -> StrategicRoadmapModel:
        self._ensure_enabled()
        details = self._executive_intelligence.get_latest(
            GetLatestExecutiveIntelligenceQuery(
                portfolio_id=query.portfolio_id,
                organization_id=query.organization_id,
                workspace_id=query.workspace_id,
            )
        )
        return self._project(details)

    def get_by_portfolio_snapshot(
        self,
        query: GetStrategicRoadmapByPortfolioSnapshotQuery,
    ) -> StrategicRoadmapModel:
        self._ensure_enabled()
        snapshot = self._executive_intelligence_repository.latest_completed_for_portfolio_snapshot(
            query.portfolio_snapshot_id
        )
        if snapshot is None:
            raise StrategicRoadmapNotFoundError(query.portfolio_snapshot_id.value)
        if (
            snapshot.organization_id != query.organization_id
            or snapshot.workspace_id != query.workspace_id
        ):
            raise StrategicRoadmapNotFoundError(query.portfolio_snapshot_id.value)
        if (
            query.portfolio_id is not None
            and snapshot.portfolio_id != query.portfolio_id
        ):
            raise StrategicRoadmapNotFoundError(query.portfolio_snapshot_id.value)
        return self._project(
            self._executive_intelligence.details_from_snapshot(snapshot)
        )

    def _project(self, details: ExecutiveIntelligenceDetails) -> StrategicRoadmapModel:
        if details.summary.status is not ExecutiveIntelligenceStatus.COMPLETED:
            raise StrategicRoadmapNotReadyError(
                "Strategic Roadmap requires a completed Executive Intelligence snapshot",
                reason_code="executive_intelligence_not_completed",
            )
        return self._builder.build(details)

    def _ensure_enabled(self) -> None:
        if not strategic_roadmap_enabled():
            raise StrategicRoadmapDisabledError(
                "Strategic Portfolio Roadmap is disabled",
                reason_code="strategic_roadmap_disabled",
            )
