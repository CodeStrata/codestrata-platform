"""Repository snapshot selection for portfolio aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.portfolio.lifecycle import (
    RepositoryAvailabilityStatus,
    RepositoryCriticality,
)
from codestrata_platform.domain.portfolio.membership import PortfolioMembership
from codestrata_platform.domain.portfolio.ports import (
    PortfolioSourceIntelligenceRepository,
    PublishedRepositoryIntelligence,
)
from codestrata_platform.domain.portfolio.snapshot import PortfolioRepositorySnapshotSelection
from codestrata_platform.domain.repository.ids import RepositoryId


@dataclass(frozen=True, slots=True)
class RepositorySnapshotSelectionPolicy:
    policy_id: str = "latest_published_repository_snapshot_v1"


class PortfolioRepositorySnapshotSelector(Protocol):
    def select(
        self,
        memberships: tuple[PortfolioMembership, ...],
    ) -> tuple[PortfolioRepositorySnapshotSelection, ...]: ...


class LatestPublishedRepositorySnapshotPolicy:
    """Select latest published EngineeringSnapshot per active portfolio repository."""

    def __init__(
        self,
        sources: PortfolioSourceIntelligenceRepository,
        *,
        policy: RepositorySnapshotSelectionPolicy | None = None,
    ) -> None:
        self._sources = sources
        self.policy = policy or RepositorySnapshotSelectionPolicy()

    def select(
        self,
        memberships: tuple[PortfolioMembership, ...],
    ) -> tuple[PortfolioRepositorySnapshotSelection, ...]:
        selections, _intelligence = self.select_with_sources(memberships)
        return selections

    def select_with_sources(
        self,
        memberships: tuple[PortfolioMembership, ...],
    ) -> tuple[
        tuple[PortfolioRepositorySnapshotSelection, ...],
        dict[str, PublishedRepositoryIntelligence],
    ]:
        selected_at = datetime.now(UTC)
        results: list[PortfolioRepositorySnapshotSelection] = []
        intelligence: dict[str, PublishedRepositoryIntelligence] = {}
        for membership in memberships:
            if not membership.is_active:
                continue
            intel = self._sources.load_latest_published(
                organization_id=membership.organization_id,
                workspace_id=membership.workspace_id,
                repository_id=membership.repository_id,
            )
            if intel is not None:
                intelligence[membership.repository_id.value] = intel
            results.append(self._to_selection(membership, intel, selected_at))
        results.sort(key=lambda item: item.repository_id.value)
        return tuple(results), intelligence

    def _to_selection(
        self,
        membership: PortfolioMembership,
        intel: PublishedRepositoryIntelligence | None,
        selected_at: datetime,
    ) -> PortfolioRepositorySnapshotSelection:
        if intel is None:
            return PortfolioRepositorySnapshotSelection(
                repository_id=membership.repository_id,
                availability_status=RepositoryAvailabilityStatus.UNAVAILABLE,
                selected_at=selected_at,
                criticality=membership.criticality,
            )
        snap = intel.engineering_snapshot
        return PortfolioRepositorySnapshotSelection(
            repository_id=membership.repository_id,
            availability_status=RepositoryAvailabilityStatus.AVAILABLE,
            selected_at=selected_at,
            criticality=membership.criticality,
            assessment_id=AssessmentId(intel.assessment_id),
            engineering_snapshot_id=snap.snapshot_id.value,
            engineering_snapshot_version=snap.version.value,
            knowledge_graph_id=intel.knowledge_graph_id,
            knowledge_graph_version=intel.knowledge_graph_version,
            graph_intelligence_policy_version=intel.graph_intelligence_policy_version,
        )


def selection_lookup(
    selections: tuple[PortfolioRepositorySnapshotSelection, ...],
) -> dict[RepositoryId, PortfolioRepositorySnapshotSelection]:
    return {item.repository_id: item for item in selections}


def criticality_for(
    memberships: tuple[PortfolioMembership, ...],
    repository_id: RepositoryId,
) -> RepositoryCriticality:
    for item in memberships:
        if item.repository_id == repository_id and item.is_active:
            return item.criticality
    return RepositoryCriticality.UNSPECIFIED
