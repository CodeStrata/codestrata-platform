"""RepositoryDrilldownDiagnostics — factual counters only."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.intelligence_reporting.domain.drilldown import (
    RepositoryIntelligenceDrilldown,
)


@dataclass(frozen=True, slots=True)
class RepositoryDrilldownDiagnostics:
    included_repository_count: int = 0
    drilldown_count: int = 0
    technology_ref_count: int = 0
    head_snapshot_count: int = 0
    finding_ref_count: int = 0
    recommendation_ref_count: int = 0
    priority_action_ref_count: int = 0
    roadmap_ref_count: int = 0
    correlation_ref_count: int = 0
    pattern_membership_count: int = 0
    modernization_membership_count: int = 0
    truncated_repository_count: int = 0
    legacy_limited_repository_count: int = 0
    public_export_eligible_count: int = 0
    anonymization_required_count: int = 0
    unresolved_reference_count: int = 0
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "limitations",
            tuple(sorted({item for item in self.limitations if item})),
        )


@dataclass(frozen=True, slots=True)
class RepositoryDrilldownResult:
    drilldowns: tuple[RepositoryIntelligenceDrilldown, ...]
    diagnostics: RepositoryDrilldownDiagnostics
    policy_token: str
