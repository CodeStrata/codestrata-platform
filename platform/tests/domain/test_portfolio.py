"""Domain tests for portfolio lifecycle and policies."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from codestrata_platform.application.portfolio.policies import (
    AssessmentFreshnessPolicy,
    ModernizationWavePolicy,
    TechnologyStandardizationPolicy,
    priority_band,
)
from codestrata_platform.domain.errors import InvalidStateTransitionError
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.errors import (
    PortfolioMembershipError,
    PortfolioSnapshotError,
)
from codestrata_platform.domain.portfolio.identifiers import PortfolioProjectionKey
from codestrata_platform.domain.portfolio.lifecycle import (
    AssessmentFreshnessStatus,
    ModernizationWave,
    PortfolioSnapshotStatus,
    PriorityBand,
    RepositoryCriticality,
    TechnologyStandardizationStatus,
)
from codestrata_platform.domain.portfolio.membership import PortfolioRepositoryReference
from codestrata_platform.domain.portfolio.portfolio import EngineeringPortfolio
from codestrata_platform.domain.portfolio.snapshot import PortfolioSnapshot
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


def test_portfolio_lifecycle_and_membership() -> None:
    portfolio = EngineeringPortfolio.create(
        organization_id=OrganizationId("org:1"),
        workspace_id=WorkspaceId("workspace:1"),
        name="Core",
    )
    membership = portfolio.add_repository(
        PortfolioRepositoryReference(
            organization_id=OrganizationId("org:1"),
            workspace_id=WorkspaceId("workspace:1"),
            repository_id=RepositoryId("repo:1"),
        ),
        criticality=RepositoryCriticality.HIGH,
    )
    assert membership.is_active
    assert len(portfolio.active_memberships) == 1
    with pytest.raises(PortfolioMembershipError, match="already"):
        portfolio.add_repository(
            PortfolioRepositoryReference(
                organization_id=OrganizationId("org:1"),
                workspace_id=WorkspaceId("workspace:1"),
                repository_id=RepositoryId("repo:1"),
            )
        )
    with pytest.raises(PortfolioMembershipError, match="same organization"):
        portfolio.add_repository(
            PortfolioRepositoryReference(
                organization_id=OrganizationId("org:2"),
                workspace_id=WorkspaceId("workspace:1"),
                repository_id=RepositoryId("repo:2"),
            )
        )
    removed = portfolio.remove_repository(RepositoryId("repo:1"))
    assert removed is not None
    assert not removed.is_active
    assert len(portfolio.active_memberships) == 0
    portfolio.archive()
    with pytest.raises(InvalidStateTransitionError):
        portfolio.add_repository(
            PortfolioRepositoryReference(
                organization_id=OrganizationId("org:1"),
                workspace_id=WorkspaceId("workspace:1"),
                repository_id=RepositoryId("repo:3"),
            )
        )


def test_projection_key_deterministic() -> None:
    key1 = PortfolioProjectionKey.from_parts(
        portfolio_id="portfolio:1",
        membership_repository_ids=("repo:b", "repo:a"),
        selected_snapshots=(("snap:2", 2), ("snap:1", 1)),
        selected_graphs=(("graph:1", 1),),
        aggregation_policy_version="v1",
        portfolio_schema_version="schema-v1",
    )
    key2 = PortfolioProjectionKey.from_parts(
        portfolio_id="portfolio:1",
        membership_repository_ids=("repo:a", "repo:b"),
        selected_snapshots=(("snap:1", 1), ("snap:2", 2)),
        selected_graphs=(("graph:1", 1),),
        aggregation_policy_version="v1",
        portfolio_schema_version="schema-v1",
    )
    assert key1.value == key2.value


def test_completed_snapshot_immutable() -> None:
    snapshot = PortfolioSnapshot.create_pending(
        portfolio_id=EngineeringPortfolio.create(
            organization_id=OrganizationId("org:1"),
            workspace_id=WorkspaceId("workspace:1"),
            name="P",
        ).portfolio_id,
        organization_id=OrganizationId("org:1"),
        workspace_id=WorkspaceId("workspace:1"),
        version=1,
        projection_key=PortfolioProjectionKey("a" * 64),
    )
    snapshot.begin_aggregation()
    snapshot.attach_technology_inventory(())
    snapshot.attach_finding_inventory((object(),))
    snapshot.attach_recommendation_inventory((object(),))
    snapshot.attach_risk_summary(object())
    snapshot.attach_modernization_summary(object())
    snapshot.attach_coverage_summary(object())
    snapshot.complete()
    assert snapshot.status is PortfolioSnapshotStatus.COMPLETED
    with pytest.raises(PortfolioSnapshotError):
        snapshot.begin_aggregation()
    snapshot.supersede()
    assert snapshot.status is PortfolioSnapshotStatus.SUPERSEDED


def test_standardization_and_freshness_and_waves() -> None:
    policy = TechnologyStandardizationPolicy()
    assert (
        policy.classify(usage_ratio=0.8, repository_count=4, fragmented=False)
        is TechnologyStandardizationStatus.STANDARD
    )
    assert (
        policy.classify(usage_ratio=0.2, repository_count=1, fragmented=False)
        is TechnologyStandardizationStatus.ISOLATED
    )
    assert (
        policy.classify(usage_ratio=0.4, repository_count=3, fragmented=True)
        is TechnologyStandardizationStatus.FRAGMENTED
    )
    freshness = AssessmentFreshnessPolicy()
    now = datetime.now(UTC)
    status, age = freshness.classify(published_at=now - timedelta(days=10), evaluated_at=now)
    assert status is AssessmentFreshnessStatus.CURRENT
    assert age == 10
    status, _ = freshness.classify(published_at=now - timedelta(days=45), evaluated_at=now)
    assert status is AssessmentFreshnessStatus.AGING
    status, _ = freshness.classify(published_at=now - timedelta(days=120), evaluated_at=now)
    assert status is AssessmentFreshnessStatus.STALE
    wave, factors = ModernizationWavePolicy().assign(
        priority_score=70,
        systemic=True,
        blocked=False,
        evidence_coverage=0.8,
    )
    assert wave is ModernizationWave.WAVE_1
    assert factors
    assert priority_band(85) is PriorityBand.CRITICAL
    assert priority_band(10) is PriorityBand.LOW
