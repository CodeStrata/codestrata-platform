"""Regression coverage for Executive Intelligence audit gap closure."""

from __future__ import annotations

from dataclasses import replace

import pytest

from codestrata_platform.application.executive_intelligence import services as exec_services
from codestrata_platform.application.executive_intelligence.aggregation import (
    run_executive_aggregation,
)
from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_intelligence.errors import (
    ExecutiveIntelligenceNotFoundError,
)
from codestrata_platform.application.executive_intelligence.queries import (
    GetExecutiveIntelligenceQuery,
    ListExecutiveIntelligenceQuery,
)
from codestrata_platform.application.portfolio.commands import (
    AddRepositoryToPortfolioCommand,
    RebuildPortfolioSnapshotCommand,
)
from codestrata_platform.domain.engineering import EngineeringCategory
from codestrata_platform.domain.executive_intelligence.identifiers import ExecutiveIntelligenceId
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveIntelligenceStatus,
    ExecutiveMetricKey,
    ExecutiveRecommendationTheme,
)
from codestrata_platform.domain.repository.ids import RepositoryId

from .test_executive_intelligence_service import (
    _build_portfolio,
    _enable_executive_intelligence,
    _seed_repository,
    _stack,
)


def test_missing_executive_intelligence_raises_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    with pytest.raises(ExecutiveIntelligenceNotFoundError) as exc:
        stack["exec_service"].get(
            GetExecutiveIntelligenceQuery(
                executive_intelligence_id=ExecutiveIntelligenceId("exec:missing"),
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )
    assert exc.value.reason_code == "executive_intelligence_not_found"


def test_failed_build_allows_successful_retry_same_projection_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="docker")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])

    real = run_executive_aggregation
    calls = {"n": 0}

    def flaky(snapshot):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("forced aggregation failure")
        return real(snapshot)

    monkeypatch.setattr(exec_services, "run_executive_aggregation", flaky)

    with pytest.raises(RuntimeError, match="forced aggregation failure"):
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
    assert len(failed) == 1
    failed_key = failed[0].projection_key.value

    completed = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert completed.summary.status.value == "completed"
    assert completed.summary.projection_key == failed_key
    assert completed.summary.executive_intelligence_id != failed[0].executive_intelligence_id.value


def test_list_pagination_total_reflects_full_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="docker")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])

    first = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )

    other = _seed_repository(stack, idx=2, tech_key="podman")
    stack["management"].add_repository(
        AddRepositoryToPortfolioCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
            repository_id=other,
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


def test_cloud_and_ai_recommendations_include_affected_repositories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    cloud_repo = _seed_repository(
        stack,
        idx=1,
        tech_key="docker",
        category=EngineeringCategory.CLOUD,
    )
    other_repo = _seed_repository(
        stack,
        idx=2,
        tech_key="java",
        category=EngineeringCategory.OTHER,
    )
    portfolio_id = _build_portfolio(stack, repo_ids=[cloud_repo, other_repo])
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )

    cloud_metric = next(
        item for item in details.metrics if item.key is ExecutiveMetricKey.CLOUD_ADOPTION
    )
    assert 0 < cloud_metric.score < 80

    cloud_recs = [
        item
        for item in details.recommendations
        if item.theme is ExecutiveRecommendationTheme.CLOUD_STRATEGY
    ]
    assert cloud_recs
    assert cloud_recs[0].affected_repository_ids
    assert cloud_repo.value in cloud_recs[0].affected_repository_ids

    ai_recs = [
        item
        for item in details.recommendations
        if item.theme is ExecutiveRecommendationTheme.AI_ADOPTION
    ]
    assert ai_recs
    assert ai_recs[0].affected_repository_ids
    assert set(ai_recs[0].affected_repository_ids) <= {
        cloud_repo.value,
        other_repo.value,
    }


def test_incomplete_coverage_discloses_snapshot_limitations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="docker")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])
    completed = stack["portfolio_snapshots"].get_latest_completed(portfolio_id)
    assert completed is not None
    coverage = completed.coverage_summary
    assert coverage is not None
    # Completed snapshots block attach_*; assign coverage for aggregation-only testing.
    completed.coverage_summary = replace(
        coverage,
        repositories_unavailable=1,
        repository_participation_percentage=50.0,
    )

    result = run_executive_aggregation(completed)
    joined = " ".join(result.limitations).lower()
    assert "unavailable" in joined
    assert "participation" in joined


def test_codestrata_dogfood_executive_intelligence_builds_cto_confidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dogfood Executive Intelligence against a CodeStrata-shaped multi-repo portfolio."""

    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    repos = [
        _seed_repository(stack, idx=1, tech_key="python"),
        _seed_repository(stack, idx=2, tech_key="fastapi"),
        _seed_repository(stack, idx=3, tech_key="postgresql"),
        _seed_repository(stack, idx=4, tech_key="docker"),
    ]
    for idx, name in enumerate(("engine", "platform", "vscode", "docs"), start=1):
        assert stack["repos"].get(RepositoryId(f"repo:{idx}")) is not None, name

    portfolio_id = _build_portfolio(stack, repo_ids=repos)
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )

    by_key = {item.key: item for item in details.metrics}
    assert set(by_key) == set(ExecutiveMetricKey)
    assert by_key[ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH].score >= 0
    assert by_key[ExecutiveMetricKey.PORTFOLIO_RISK].confidence > 0.15
    assert by_key[ExecutiveMetricKey.MODERNIZATION_READINESS].inputs
    assert by_key[ExecutiveMetricKey.ARCHITECTURE_MATURITY].calculation_rule
    assert by_key[ExecutiveMetricKey.TECHNOLOGY_STANDARDIZATION].score >= 0
    assert details.limitations
    for recommendation in details.recommendations:
        assert recommendation.rationale
        assert recommendation.expected_impact
        assert 0 <= recommendation.priority_score <= 100
    assert details.summary.status.value == "completed"
