"""Application-scale dogfood for Phase 8.8.5 (10-repo portfolio)."""

from __future__ import annotations

import time

import pytest

from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_presentation.queries import (
    GetLatestExecutivePresentationQuery,
)
from codestrata_platform.application.executive_presentation.services import (
    ExecutivePresentationService,
)
from codestrata_platform.application.strategic_roadmap.builder import StrategicRoadmapBuilder
from codestrata_platform.application.strategic_roadmap.queries import (
    GetLatestStrategicRoadmapQuery,
)
from codestrata_platform.application.strategic_roadmap.services import StrategicRoadmapService
from codestrata_platform.domain.engineering import EngineeringCategory

from .test_executive_intelligence_service import (
    _build_portfolio,
    _enable_executive_intelligence,
    _seed_repository,
)
from .test_executive_intelligence_service import (
    _stack as _exec_stack,
)
from .test_executive_presentation import _enable_presentation
from .test_strategic_roadmap import _enable_roadmap


def test_ten_repository_portfolio_executive_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    _enable_presentation(monkeypatch)
    _enable_roadmap(monkeypatch)
    stack = _exec_stack()
    repos = [
        _seed_repository(
            stack,
            idx=i,
            tech_key=f"tech-{i}",
            category=(
                EngineeringCategory.SECURITY
                if i % 3 == 0
                else EngineeringCategory.ARCHITECTURE
            ),
        )
        for i in range(1, 11)
    ]
    portfolio_id = _build_portfolio(stack, repo_ids=repos)
    t0 = time.perf_counter()
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    build_ms = (time.perf_counter() - t0) * 1000
    assert details.summary.status.value == "completed"
    assert details.findings
    assert details.metrics

    presentation = ExecutivePresentationService(
        executive_intelligence=stack["exec_service"],
        executive_intelligence_repository=stack["executive_intelligence"],
    )
    roadmap = StrategicRoadmapService(
        executive_intelligence=stack["exec_service"],
        executive_intelligence_repository=stack["executive_intelligence"],
    )
    query = dict(
        portfolio_id=portfolio_id,
        organization_id=stack["org"].organization_id,
        workspace_id=stack["workspace"].workspace_id,
    )
    first_presentation = presentation.get_latest(GetLatestExecutivePresentationQuery(**query))
    second_presentation = presentation.get_latest(GetLatestExecutivePresentationQuery(**query))
    assert first_presentation.identity.executive_intelligence_id == (
        details.summary.executive_intelligence_id
    )
    assert (
        first_presentation.identity.executive_intelligence_id
        == second_presentation.identity.executive_intelligence_id
    )

    first_roadmap = roadmap.get_latest(GetLatestStrategicRoadmapQuery(**query))
    second_roadmap = roadmap.get_latest(GetLatestStrategicRoadmapQuery(**query))
    built = StrategicRoadmapBuilder().build(details)
    assert [item.initiative_id for item in first_roadmap.initiatives] == [
        item.initiative_id for item in second_roadmap.initiatives
    ]
    assert [item.initiative_id for item in built.initiatives] == [
        item.initiative_id for item in first_roadmap.initiatives
    ]
    for initiative in built.initiatives:
        assert initiative.depends_on_initiative_ids == ()
        if initiative.supporting_recommendation_ids:
            assert initiative.supporting_finding_ids == ()
    # Soft timing observation only.
    assert build_ms < 5000
