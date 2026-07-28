"""Reliability and recovery hardening regressions (Phase 8.8.2)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from codestrata_platform.application.common.errors import ValidationError
from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_intelligence.errors import (
    ExecutiveIntelligenceDisabledError,
)
from codestrata_platform.application.knowledge_graph.commands import BuildKnowledgeGraphCommand
from codestrata_platform.application.knowledge_graph.projection import project_snapshot_into_graph
from codestrata_platform.application.knowledge_graph.services import (
    EngineeringGraphProjectionService,
)
from codestrata_platform.application.portfolio import services as portfolio_services
from codestrata_platform.application.portfolio.commands import (
    AddRepositoryToPortfolioCommand,
    BuildPortfolioSnapshotCommand,
    CreatePortfolioCommand,
)
from codestrata_platform.application.strategic_roadmap.builder import StrategicRoadmapBuilder
from codestrata_platform.application.strategic_roadmap.queries import GetStrategicRoadmapQuery
from codestrata_platform.application.strategic_roadmap.services import StrategicRoadmapService
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveIntelligenceStatus,
)
from codestrata_platform.domain.knowledge_graph.lifecycle import GraphStatus
from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio.lifecycle import PortfolioSnapshotStatus
from codestrata_platform.infrastructure.memory import (
    InMemoryEngineeringSnapshotRepository,
    InMemoryKnowledgeGraphRepository,
)

from .test_executive_intelligence_service import (
    _build_portfolio,
    _enable_executive_intelligence,
    _seed_repository,
)
from .test_executive_intelligence_service import (
    _stack as _exec_stack,
)
from .test_knowledge_graph_service import _published_snapshot
from .test_portfolio_service import _stack as _portfolio_stack
from .test_strategic_roadmap import _enable_roadmap


def test_knowledge_graph_failed_build_allows_deterministic_retry() -> None:
    snapshots = InMemoryEngineeringSnapshotRepository()
    graphs = InMemoryKnowledgeGraphRepository()
    snapshot = _published_snapshot()
    snapshots.save(snapshot)
    service = EngineeringGraphProjectionService(
        graphs=graphs,
        snapshots=snapshots,
        queries=graphs,
    )

    real = project_snapshot_into_graph
    calls = {"n": 0}

    def flaky(graph, published):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("forced graph projection failure")
        return real(graph, published)

    with patch(
        "codestrata_platform.application.knowledge_graph.services.project_snapshot_into_graph",
        flaky,
    ):
        with pytest.raises(ValidationError, match="forced graph projection failure"):
            service.build_knowledge_graph(
                BuildKnowledgeGraphCommand(snapshot_id=snapshot.snapshot_id)
            )

    failed = [
        item
        for item in graphs._items.values()  # noqa: SLF001
        if item.status is GraphStatus.FAILED
    ]
    assert len(failed) == 1
    assert ":f" in failed[0].projection_key.value

    recovered = service.build_knowledge_graph(
        BuildKnowledgeGraphCommand(snapshot_id=snapshot.snapshot_id)
    )
    assert recovered.created is True
    assert recovered.graph.status is GraphStatus.COMPLETED

    again = service.build_knowledge_graph(
        BuildKnowledgeGraphCommand(snapshot_id=snapshot.snapshot_id)
    )
    assert again.idempotent is True
    assert again.graph.graph_id == recovered.graph.graph_id


def test_portfolio_snapshot_failed_build_allows_deterministic_retry() -> None:
    management, aggregation, org, workspace, repo_ids = _portfolio_stack()
    created = management.create_portfolio(
        CreatePortfolioCommand(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            name="Reliability",
        )
    )
    portfolio_id = PortfolioId(created.summary.portfolio_id)
    for repo_id in repo_ids[:2]:
        management.add_repository(
            AddRepositoryToPortfolioCommand(
                portfolio_id=portfolio_id,
                organization_id=org.organization_id,
                workspace_id=workspace.workspace_id,
                repository_id=repo_id,
            )
        )

    real = portfolio_services.run_aggregation
    calls = {"n": 0}

    def flaky(context):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("forced portfolio aggregation failure")
        return real(context)

    with patch(
        "codestrata_platform.application.portfolio.services.run_aggregation",
        flaky,
    ):
        with pytest.raises(RuntimeError, match="forced portfolio aggregation failure"):
            aggregation.build_snapshot(
                BuildPortfolioSnapshotCommand(
                    portfolio_id=portfolio_id,
                    organization_id=org.organization_id,
                    workspace_id=workspace.workspace_id,
                )
            )

    failed = [
        item
        for item in aggregation._snapshots._items.values()  # noqa: SLF001
        if item.status is PortfolioSnapshotStatus.FAILED
    ]
    assert len(failed) == 1
    assert ":f" in failed[0].projection_key.value

    recovered = aggregation.build_snapshot(
        BuildPortfolioSnapshotCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    assert recovered.summary.status is PortfolioSnapshotStatus.COMPLETED

    again = aggregation.build_snapshot(
        BuildPortfolioSnapshotCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    assert again.summary.portfolio_snapshot_id == recovered.summary.portfolio_snapshot_id


def test_executive_failed_then_retry_and_idempotent_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _exec_stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="python")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])

    from codestrata_platform.application.executive_intelligence import (
        services as exec_services,
    )
    from codestrata_platform.application.executive_intelligence.aggregation import (
        run_executive_aggregation,
    )

    real = run_executive_aggregation
    calls = {"n": 0}

    def flaky(snapshot):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("forced executive failure")
        return real(snapshot)

    monkeypatch.setattr(exec_services, "run_executive_aggregation", flaky)

    with pytest.raises(RuntimeError, match="forced executive failure"):
        stack["exec_service"].build_intelligence(
            BuildExecutiveIntelligenceCommand(
                portfolio_id=portfolio_id,
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )
    failed = [
        item
        for item in stack["executive_intelligence"]._items.values()  # noqa: SLF001
        if item.status is ExecutiveIntelligenceStatus.FAILED
    ]
    assert failed

    first = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
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
    assert first.summary.executive_intelligence_id == (
        second.summary.executive_intelligence_id
    )
    assert first.summary.status is ExecutiveIntelligenceStatus.COMPLETED


def test_roadmap_repeated_generation_is_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    _enable_roadmap(monkeypatch)
    stack = _exec_stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="fastapi")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])
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
    query = GetStrategicRoadmapQuery(
        executive_intelligence_id=ExecutiveIntelligenceId(
            details.summary.executive_intelligence_id
        ),
        organization_id=stack["org"].organization_id,
        workspace_id=stack["workspace"].workspace_id,
    )
    first = service.get(query)
    second = service.get(query)
    builder_first = StrategicRoadmapBuilder().build(details)
    builder_second = StrategicRoadmapBuilder().build(details)
    assert [item.initiative_id for item in first.initiatives] == [
        item.initiative_id for item in second.initiatives
    ]
    assert [item.initiative_id for item in builder_first.initiatives] == [
        item.initiative_id for item in builder_second.initiatives
    ]
    assert first.summary.initiative_count == len(first.initiatives)


def test_disabled_executive_flag_does_not_persist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", raising=False)
    stack = _exec_stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="docker")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])

    with pytest.raises(ExecutiveIntelligenceDisabledError):
        stack["exec_service"].build_intelligence(
            BuildExecutiveIntelligenceCommand(
                portfolio_id=portfolio_id,
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )
    assert stack["executive_intelligence"]._items == {}  # noqa: SLF001
