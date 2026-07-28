"""Strategic Portfolio Roadmap builder and service tests."""

from __future__ import annotations

import pytest

from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_intelligence.errors import (
    ExecutiveIntelligenceNotFoundError,
)
from codestrata_platform.application.strategic_roadmap.builder import (
    StrategicRoadmapBuilder,
)
from codestrata_platform.application.strategic_roadmap.errors import (
    StrategicRoadmapDisabledError,
    StrategicRoadmapNotFoundError,
)
from codestrata_platform.application.strategic_roadmap.models import (
    RoadmapEffortBand,
    RoadmapWave,
)
from codestrata_platform.application.strategic_roadmap.queries import (
    GetLatestStrategicRoadmapQuery,
    GetStrategicRoadmapByPortfolioSnapshotQuery,
    GetStrategicRoadmapQuery,
)
from codestrata_platform.application.strategic_roadmap.services import (
    StrategicRoadmapService,
)
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.portfolio.identifiers import PortfolioSnapshotId
from codestrata_platform.domain.workspace.ids import WorkspaceId

from .test_executive_intelligence_service import (
    _build_portfolio,
    _enable_executive_intelligence,
    _seed_repository,
    _stack,
)


def _enable_roadmap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_STRATEGIC_ROADMAP_ENABLED", "true")


def _build_roadmap_stack(monkeypatch: pytest.MonkeyPatch, *, repo_count: int = 1):
    _enable_executive_intelligence(monkeypatch)
    _enable_roadmap(monkeypatch)
    stack = _stack()
    repos = [
        _seed_repository(stack, idx=i, tech_key=f"tech-{i}")
        for i in range(1, repo_count + 1)
    ]
    portfolio_id = _build_portfolio(stack, repo_ids=repos)
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    service = StrategicRoadmapService(
        executive_intelligence=stack["exec_service"],
        executive_intelligence_repository=stack["executive_intelligence"],
    )
    return stack, portfolio_id, details, service


def test_roadmap_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODESTRATA_STRATEGIC_ROADMAP_ENABLED", raising=False)
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="docker")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])
    stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    service = StrategicRoadmapService(
        executive_intelligence=stack["exec_service"],
        executive_intelligence_repository=stack["executive_intelligence"],
    )
    with pytest.raises(StrategicRoadmapDisabledError):
        service.get_latest(
            GetLatestStrategicRoadmapQuery(
                portfolio_id=portfolio_id,
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )


def test_empty_portfolio_roadmap_has_no_invented_initiatives(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    _enable_roadmap(monkeypatch)
    stack = _stack()
    portfolio_id = _build_portfolio(stack, repo_ids=[])
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    model = StrategicRoadmapBuilder().build(details)
    assert model.summary.initiative_count == len(model.initiatives)
    assert model.limitations == details.limitations
    assert all(item.depends_on_initiative_ids == () for item in model.initiatives)
    assert {bucket.wave for bucket in model.waves} == set(RoadmapWave)


def test_single_and_mixed_portfolio_initiatives_are_evidence_backed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stack, _, details, service = _build_roadmap_stack(monkeypatch, repo_count=1)
    single = service.get(
        GetStrategicRoadmapQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(
                details.summary.executive_intelligence_id
            ),
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert single.summary.initiative_count == len(single.initiatives)
    rec_ids = {item.recommendation_id.value for item in details.recommendations}
    finding_ids = {item.finding_id.value for item in details.findings}
    for initiative in single.initiatives:
        assert 0 <= initiative.priority <= 100
        assert initiative.effort_band in set(RoadmapEffortBand)
        assert initiative.sequencing_wave in set(RoadmapWave)
        assert initiative.confidence >= 0.0
        assert initiative.coverage >= 0.0
        assert initiative.priority_inputs
        assert initiative.effort_rule
        assert initiative.wave_rule
        assert initiative.depends_on_initiative_ids == ()
        for finding_id in initiative.supporting_finding_ids:
            assert finding_id in finding_ids
        for recommendation_id in initiative.supporting_recommendation_ids:
            assert recommendation_id in rec_ids

    mixed_stack, _, mixed_details, mixed_service = _build_roadmap_stack(
        monkeypatch, repo_count=3
    )
    mixed = mixed_service.get(
        GetStrategicRoadmapQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(
                mixed_details.summary.executive_intelligence_id
            ),
            organization_id=mixed_stack["org"].organization_id,
            workspace_id=mixed_stack["workspace"].workspace_id,
        )
    )
    assert mixed.initiatives
    assert mixed.summary.effort_distribution
    assert mixed.summary.wave_distribution
    assert mixed.summary.category_distribution
    priorities = [item.priority for item in mixed.initiatives]
    assert priorities == sorted(priorities, reverse=True)


def test_roadmap_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    _, _, details, _ = _build_roadmap_stack(monkeypatch, repo_count=2)
    first = StrategicRoadmapBuilder().build(details)
    second = StrategicRoadmapBuilder().build(details)
    assert [item.initiative_id for item in first.initiatives] == [
        item.initiative_id for item in second.initiatives
    ]
    assert [item.priority for item in first.initiatives] == [
        item.priority for item in second.initiatives
    ]
    assert [item.sequencing_wave for item in first.initiatives] == [
        item.sequencing_wave for item in second.initiatives
    ]


def test_tenant_isolation_and_lookups(monkeypatch: pytest.MonkeyPatch) -> None:
    stack, portfolio_id, details, service = _build_roadmap_stack(monkeypatch)
    latest = service.get_latest(
        GetLatestStrategicRoadmapQuery(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert (
        latest.identity.executive_intelligence_id
        == details.summary.executive_intelligence_id
    )
    by_snapshot = service.get_by_portfolio_snapshot(
        GetStrategicRoadmapByPortfolioSnapshotQuery(
            portfolio_snapshot_id=PortfolioSnapshotId(details.summary.portfolio_snapshot_id),
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
            portfolio_id=portfolio_id,
        )
    )
    assert (
        by_snapshot.identity.executive_intelligence_id
        == details.summary.executive_intelligence_id
    )
    with pytest.raises(ExecutiveIntelligenceNotFoundError):
        service.get(
            GetStrategicRoadmapQuery(
                executive_intelligence_id=ExecutiveIntelligenceId(
                    details.summary.executive_intelligence_id
                ),
                organization_id=stack["org"].organization_id,
                workspace_id=WorkspaceId("workspace:other"),
            )
        )
    with pytest.raises(StrategicRoadmapNotFoundError):
        service.get_by_portfolio_snapshot(
            GetStrategicRoadmapByPortfolioSnapshotQuery(
                portfolio_snapshot_id=PortfolioSnapshotId("portfolio-snapshot:missing"),
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )
