"""Executive Presentation application services (on-read projection)."""

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
from codestrata_platform.application.executive_presentation.adapter import (
    ExecutivePresentationAdapter,
)
from codestrata_platform.application.executive_presentation.errors import (
    ExecutivePresentationDisabledError,
    ExecutivePresentationNotFoundError,
    ExecutivePresentationNotReadyError,
)
from codestrata_platform.application.executive_presentation.models import (
    ExecutivePresentationModel,
)
from codestrata_platform.application.executive_presentation.policies import (
    executive_presentation_enabled,
)
from codestrata_platform.application.executive_presentation.queries import (
    GetExecutivePresentationByPortfolioSnapshotQuery,
    GetExecutivePresentationQuery,
    GetLatestExecutivePresentationQuery,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveIntelligenceStatus,
)
from codestrata_platform.domain.executive_intelligence.ports import (
    ExecutiveIntelligenceRepository,
)


class ExecutivePresentationService:
    """Load completed Executive Intelligence and project presentation models on read."""

    def __init__(
        self,
        *,
        executive_intelligence: ExecutiveIntelligenceAggregationService,
        executive_intelligence_repository: ExecutiveIntelligenceRepository,
        adapter: ExecutivePresentationAdapter | None = None,
    ) -> None:
        self._executive_intelligence = executive_intelligence
        self._executive_intelligence_repository = executive_intelligence_repository
        self._adapter = adapter or ExecutivePresentationAdapter()

    def get(self, query: GetExecutivePresentationQuery) -> ExecutivePresentationModel:
        self._ensure_enabled()
        details = self._executive_intelligence.get(
            GetExecutiveIntelligenceQuery(
                executive_intelligence_id=query.executive_intelligence_id,
                organization_id=query.organization_id,
                workspace_id=query.workspace_id,
            )
        )
        return self._project(details)

    def get_latest(
        self,
        query: GetLatestExecutivePresentationQuery,
    ) -> ExecutivePresentationModel:
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
        query: GetExecutivePresentationByPortfolioSnapshotQuery,
    ) -> ExecutivePresentationModel:
        self._ensure_enabled()
        snapshot = self._executive_intelligence_repository.latest_completed_for_portfolio_snapshot(
            query.portfolio_snapshot_id
        )
        if snapshot is None:
            raise ExecutivePresentationNotFoundError(query.portfolio_snapshot_id.value)
        if (
            snapshot.organization_id != query.organization_id
            or snapshot.workspace_id != query.workspace_id
        ):
            raise ExecutivePresentationNotFoundError(query.portfolio_snapshot_id.value)
        if (
            query.portfolio_id is not None
            and snapshot.portfolio_id != query.portfolio_id
        ):
            raise ExecutivePresentationNotFoundError(query.portfolio_snapshot_id.value)
        return self._project(
            self._executive_intelligence.details_from_snapshot(snapshot)
        )

    def _project(self, details: ExecutiveIntelligenceDetails) -> ExecutivePresentationModel:
        if details.summary.status is not ExecutiveIntelligenceStatus.COMPLETED:
            raise ExecutivePresentationNotReadyError(
                "Executive Presentation requires a completed Executive Intelligence snapshot",
                reason_code="executive_intelligence_not_completed",
            )
        return self._adapter.adapt(details)

    def _ensure_enabled(self) -> None:
        if not executive_presentation_enabled():
            raise ExecutivePresentationDisabledError(
                "Executive Presentation is disabled",
                reason_code="executive_presentation_disabled",
            )
