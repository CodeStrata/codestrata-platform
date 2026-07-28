"""Performance and scalability hardening regressions (Phase 8.8.3)."""

from __future__ import annotations

import pytest

from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_intelligence.queries import (
    ListExecutiveIntelligenceQuery,
)
from codestrata_platform.application.executive_presentation.queries import (
    GetExecutivePresentationByPortfolioSnapshotQuery,
)
from codestrata_platform.application.executive_presentation.services import (
    ExecutivePresentationService,
)
from codestrata_platform.application.portfolio.commands import (
    AddRepositoryToPortfolioCommand,
    BuildPortfolioSnapshotCommand,
    CreatePortfolioCommand,
    RebuildPortfolioSnapshotCommand,
)
from codestrata_platform.application.portfolio.selection import (
    LatestPublishedRepositorySnapshotPolicy,
)
from codestrata_platform.application.strategic_roadmap.builder import (
    StrategicRoadmapBuilder,
    _related_by_shared_repositories,
)
from codestrata_platform.application.strategic_roadmap.models import (
    RoadmapEffortBand,
    RoadmapInitiative,
    RoadmapInitiativeCategory,
    RoadmapWave,
)
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId

from .test_executive_intelligence_service import (
    _build_portfolio,
    _enable_executive_intelligence,
    _seed_repository,
)
from .test_executive_intelligence_service import (
    _stack as _exec_stack,
)
from .test_executive_presentation import _enable_presentation
from .test_portfolio_service import _stack as _portfolio_stack


def test_executive_list_pagination_total_without_loading_full_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _exec_stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="python")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])
    first = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    stack["management"].add_repository(
        AddRepositoryToPortfolioCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
            repository_id=_seed_repository(stack, idx=2, tech_key="fastapi"),
        )
    )
    stack["portfolio_aggregation"].rebuild_snapshot(
        RebuildPortfolioSnapshotCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    second = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert second.summary.executive_intelligence_id != first.summary.executive_intelligence_id

    calls = {"list": 0, "count": 0}
    real_list = stack["executive_intelligence"].list_by_portfolio
    real_count = stack["executive_intelligence"].count_by_portfolio

    def counting_list(*args, **kwargs):
        calls["list"] += 1
        result = real_list(*args, **kwargs)
        assert kwargs.get("limit", 50) <= 500
        assert len(result) <= kwargs.get("limit", 50)
        return result

    def counting_count(*args, **kwargs):
        calls["count"] += 1
        return real_count(*args, **kwargs)

    monkeypatch.setattr(stack["executive_intelligence"], "list_by_portfolio", counting_list)
    monkeypatch.setattr(stack["executive_intelligence"], "count_by_portfolio", counting_count)

    page = stack["exec_service"].list_by_portfolio(
        ListExecutiveIntelligenceQuery(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
            offset=0,
            limit=1,
        )
    )
    assert page.total == 2
    assert len(page.items) == 1
    assert page.has_more is True
    assert calls["count"] == 1
    assert calls["list"] == 1


def test_portfolio_selector_loads_sources_once_per_membership() -> None:
    management, aggregation, org, workspace, repo_ids = _portfolio_stack()
    created = management.create_portfolio(
        CreatePortfolioCommand(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            name="Perf",
        )
    )
    portfolio_id = PortfolioId(created.summary.portfolio_id)
    for repo_id in repo_ids[:3]:
        management.add_repository(
            AddRepositoryToPortfolioCommand(
                portfolio_id=portfolio_id,
                organization_id=org.organization_id,
                workspace_id=workspace.workspace_id,
                repository_id=repo_id,
            )
        )

    sources = aggregation._sources  # noqa: SLF001
    real = sources.load_latest_published
    calls = {"n": 0}

    def counting(**kwargs):
        calls["n"] += 1
        return real(**kwargs)

    sources.load_latest_published = counting  # type: ignore[method-assign]
    aggregation.build_snapshot(
        BuildPortfolioSnapshotCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    assert calls["n"] == 3


def test_presentation_by_snapshot_avoids_second_get(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    _enable_presentation(monkeypatch)
    stack = _exec_stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="docker")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    service = ExecutivePresentationService(
        executive_intelligence=stack["exec_service"],
        executive_intelligence_repository=stack["executive_intelligence"],
    )
    get_calls = {"n": 0}
    real_get = stack["exec_service"].get

    def counting_get(query):
        get_calls["n"] += 1
        return real_get(query)

    monkeypatch.setattr(stack["exec_service"], "get", counting_get)
    model = service.get_by_portfolio_snapshot(
        GetExecutivePresentationByPortfolioSnapshotQuery(
            portfolio_snapshot_id=PortfolioSnapshotId(details.summary.portfolio_snapshot_id),
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
            portfolio_id=portfolio_id,
        )
    )
    assert model.identity.executive_intelligence_id == (
        details.summary.executive_intelligence_id
    )
    assert get_calls["n"] == 0


def test_roadmap_related_ids_match_shared_repo_semantics() -> None:
    initiatives = (
        RoadmapInitiative(
            initiative_id="a",
            title="A",
            category=RoadmapInitiativeCategory.SECURITY,
            description="a",
            rationale="a",
            affected_repository_ids=("repo:1", "repo:2"),
            supporting_finding_ids=(),
            supporting_recommendation_ids=(),
            expected_impact="high",
            confidence=0.5,
            confidence_band="medium",
            coverage=0.5,
            limitations=(),
            priority=80,
            effort_band=RoadmapEffortBand.SMALL,
            sequencing_wave=RoadmapWave.WAVE_1,
            related_initiative_ids=(),
            depends_on_initiative_ids=(),
            priority_inputs=("p",),
            effort_rule="e",
            wave_rule="w",
        ),
        RoadmapInitiative(
            initiative_id="b",
            title="B",
            category=RoadmapInitiativeCategory.DEPENDENCY,
            description="b",
            rationale="b",
            affected_repository_ids=("repo:2",),
            supporting_finding_ids=(),
            supporting_recommendation_ids=(),
            expected_impact="high",
            confidence=0.5,
            confidence_band="medium",
            coverage=0.5,
            limitations=(),
            priority=70,
            effort_band=RoadmapEffortBand.SMALL,
            sequencing_wave=RoadmapWave.WAVE_1,
            related_initiative_ids=(),
            depends_on_initiative_ids=(),
            priority_inputs=("p",),
            effort_rule="e",
            wave_rule="w",
        ),
        RoadmapInitiative(
            initiative_id="c",
            title="C",
            category=RoadmapInitiativeCategory.GOVERNANCE,
            description="c",
            rationale="c",
            affected_repository_ids=("repo:9",),
            supporting_finding_ids=(),
            supporting_recommendation_ids=(),
            expected_impact="low",
            confidence=0.5,
            confidence_band="medium",
            coverage=0.5,
            limitations=(),
            priority=10,
            effort_band=RoadmapEffortBand.SMALL,
            sequencing_wave=RoadmapWave.WAVE_4,
            related_initiative_ids=(),
            depends_on_initiative_ids=(),
            priority_inputs=("p",),
            effort_rule="e",
            wave_rule="w",
        ),
    )
    related = _related_by_shared_repositories(initiatives)
    by_id = {item.initiative_id: item for item in related}
    assert by_id["a"].related_initiative_ids == ("b",)
    assert by_id["b"].related_initiative_ids == ("a",)
    assert by_id["c"].related_initiative_ids == ()


def test_repeated_roadmap_generation_is_identical_at_portfolio_scale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _exec_stack()
    repos = [
        _seed_repository(stack, idx=i, tech_key=f"tech-{i}")
        for i in range(1, 11)
    ]
    portfolio_id = _build_portfolio(stack, repo_ids=repos)
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    first = StrategicRoadmapBuilder().build(details)
    second = StrategicRoadmapBuilder().build(details)
    assert [item.initiative_id for item in first.initiatives] == [
        item.initiative_id for item in second.initiatives
    ]
    assert [item.related_initiative_ids for item in first.initiatives] == [
        item.related_initiative_ids for item in second.initiatives
    ]


def test_disabled_executive_intelligence_short_circuits_before_repository_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", raising=False)
    stack = _exec_stack()
    calls = {"n": 0}
    real_get = stack["portfolio_snapshots"].get_latest_completed

    def counting(portfolio_id):
        calls["n"] += 1
        return real_get(portfolio_id)

    monkeypatch.setattr(stack["portfolio_snapshots"], "get_latest_completed", counting)
    with pytest.raises(Exception) as exc_info:
        stack["exec_service"].build_intelligence(
            BuildExecutiveIntelligenceCommand(
                portfolio_id=PortfolioId("portfolio:missing"),
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )
    assert getattr(exc_info.value, "reason_code", "") == "executive_intelligence_disabled"
    assert calls["n"] == 0


def test_portfolio_snapshot_list_pagination_uses_count() -> None:
    management, aggregation, org, workspace, repo_ids = _portfolio_stack()
    created = management.create_portfolio(
        CreatePortfolioCommand(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            name="Pages",
        )
    )
    portfolio_id = PortfolioId(created.summary.portfolio_id)
    management.add_repository(
        AddRepositoryToPortfolioCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            repository_id=repo_ids[0],
        )
    )
    aggregation.build_snapshot(
        BuildPortfolioSnapshotCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    management.add_repository(
        AddRepositoryToPortfolioCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            repository_id=repo_ids[1],
        )
    )
    aggregation.rebuild_snapshot(
        RebuildPortfolioSnapshotCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    from codestrata_platform.application.portfolio.queries import ListPortfolioSnapshotsQuery

    page = aggregation.list_snapshots(
        ListPortfolioSnapshotsQuery(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            offset=0,
            limit=1,
        )
    )
    assert page.total >= 2
    assert len(page.items) == 1
    assert page.has_more is True


def test_selector_with_sources_matches_select() -> None:
    management, aggregation, org, workspace, repo_ids = _portfolio_stack()
    created = management.create_portfolio(
        CreatePortfolioCommand(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            name="Select",
        )
    )
    portfolio_id = PortfolioId(created.summary.portfolio_id)
    management.add_repository(
        AddRepositoryToPortfolioCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            repository_id=repo_ids[0],
        )
    )
    memberships = aggregation._portfolios.get(portfolio_id).active_memberships  # noqa: SLF001
    policy = LatestPublishedRepositorySnapshotPolicy(aggregation._sources)  # noqa: SLF001
    both, intelligence = policy.select_with_sources(memberships)
    only = policy.select(memberships)
    assert [item.repository_id for item in only] == [item.repository_id for item in both]
    assert [item.availability_status for item in only] == [
        item.availability_status for item in both
    ]
    assert [item.assessment_id for item in only] == [item.assessment_id for item in both]
    assert set(intelligence).issubset({item.repository_id.value for item in both})
