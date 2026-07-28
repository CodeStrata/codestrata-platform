"""Executive Presentation projection and service tests."""

from __future__ import annotations

import pytest

from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_presentation.adapter import (
    ExecutivePresentationAdapter,
    score_status_for_metric,
)
from codestrata_platform.application.executive_presentation.errors import (
    ExecutivePresentationDisabledError,
    ExecutivePresentationNotFoundError,
)
from codestrata_platform.application.executive_presentation.models import (
    PresentationScoreStatus,
    PresentationTrendDirection,
)
from codestrata_platform.application.executive_presentation.queries import (
    GetExecutivePresentationByPortfolioSnapshotQuery,
    GetExecutivePresentationQuery,
    GetLatestExecutivePresentationQuery,
)
from codestrata_platform.application.executive_presentation.services import (
    ExecutivePresentationService,
)
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveMetricKey,
)
from codestrata_platform.domain.portfolio.identifiers import PortfolioSnapshotId

from .test_executive_intelligence_service import (
    _build_portfolio,
    _enable_executive_intelligence,
    _seed_repository,
    _stack,
)


def _enable_presentation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_EXECUTIVE_PRESENTATION_ENABLED", "true")


def _build_presentation_stack(monkeypatch: pytest.MonkeyPatch):
    _enable_executive_intelligence(monkeypatch)
    _enable_presentation(monkeypatch)
    stack = _stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="docker")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    presentation = ExecutivePresentationService(
        executive_intelligence=stack["exec_service"],
        executive_intelligence_repository=stack["executive_intelligence"],
    )
    return stack, portfolio_id, details, presentation


def test_presentation_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODESTRATA_EXECUTIVE_PRESENTATION_ENABLED", raising=False)
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
    service = ExecutivePresentationService(
        executive_intelligence=stack["exec_service"],
        executive_intelligence_repository=stack["executive_intelligence"],
    )
    with pytest.raises(ExecutivePresentationDisabledError):
        service.get_latest(
            GetLatestExecutivePresentationQuery(
                portfolio_id=portfolio_id,
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )


def test_score_status_bands_are_deterministic() -> None:
    assert (
        score_status_for_metric(ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH, 90)
        is PresentationScoreStatus.EXCELLENT
    )
    assert (
        score_status_for_metric(ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH, 0)
        is PresentationScoreStatus.CRITICAL
    )
    # Inverted: high risk score is critical.
    assert (
        score_status_for_metric(ExecutiveMetricKey.PORTFOLIO_RISK, 95)
        is PresentationScoreStatus.CRITICAL
    )
    assert (
        score_status_for_metric(ExecutiveMetricKey.PORTFOLIO_RISK, 5)
        is PresentationScoreStatus.EXCELLENT
    )


def test_presentation_preserves_source_metric_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stack, _, details, service = _build_presentation_stack(monkeypatch)
    model = service.get(
        GetExecutivePresentationQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(
                details.summary.executive_intelligence_id
            ),
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    source_by_key = {item.key: item for item in details.metrics}
    assert len(model.kpi_cards) == len(details.metrics)
    for card, source_metric in zip(model.kpi_cards, details.metrics, strict=True):
        assert card.metric_key is source_metric.key
        assert card.score == source_metric.score
        assert card.confidence == source_metric.confidence
        assert card.coverage == source_metric.coverage
        assert card.calculation_disclosure == source_metric.calculation_rule
        assert card.limitations == source_metric.limitations
        assert card.inputs == source_metric.inputs
        assert card.score == source_by_key[card.metric_key].score

    assert model.limitations_and_assumptions == details.limitations
    assert len(model.findings) == len(details.findings)
    assert len(model.recommendations) == len(details.recommendations)
    for finding, source in zip(model.findings, details.findings, strict=True):
        assert finding.finding_id == source.finding_id.value
        assert finding.title == source.title
        assert finding.description == source.summary
        assert finding.affected_repository_ids == source.affected_repository_ids
        assert finding.confidence == source.confidence
    for rec, source in zip(model.recommendations, details.recommendations, strict=True):
        assert rec.recommendation_id == source.recommendation_id.value
        assert rec.priority_score == source.priority_score
        assert rec.rationale == source.rationale
        assert rec.affected_repository_ids == source.affected_repository_ids


def test_presentation_does_not_recalculate_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, details, _ = _build_presentation_stack(monkeypatch)
    first = ExecutivePresentationAdapter().adapt(details)
    second = ExecutivePresentationAdapter().adapt(details)
    assert [card.score for card in first.kpi_cards] == [
        card.score for card in second.kpi_cards
    ]
    assert [item.key.value for item in details.metrics] == [
        card.metric_key.value for card in first.kpi_cards
    ]


def test_executive_and_cto_views(monkeypatch: pytest.MonkeyPatch) -> None:
    stack, _, details, service = _build_presentation_stack(monkeypatch)
    model = service.get(
        GetExecutivePresentationQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(
                details.summary.executive_intelligence_id
            ),
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert model.executive_summary.headline
    assert model.executive_summary.overall_engineering_health == next(
        item.score
        for item in details.metrics
        if item.key is ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH
    )
    assert model.executive_summary.modernization_outlook
    assert model.executive_summary.confidence_statement
    assert model.executive_summary.coverage_statement
    assert model.cto_summary.engineering_health.score == (
        model.executive_summary.overall_engineering_health
    )
    assert model.cto_summary.architecture_maturity.metric_key is (
        ExecutiveMetricKey.ARCHITECTURE_MATURITY
    )
    assert model.portfolio_scorecard.cards
    assert model.trend_ready_metrics
    assert all(
        point.direction is PresentationTrendDirection.UNKNOWN
        for point in model.trend_ready_metrics
    )


def test_zero_scores_and_limitations_are_visible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    _enable_presentation(monkeypatch)
    stack = _stack()
    portfolio_id = _build_portfolio(stack, repo_ids=[])
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
    model = service.get(
        GetExecutivePresentationQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(
                details.summary.executive_intelligence_id
            ),
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert any(card.score == 0 for card in model.kpi_cards)
    assert model.limitations_and_assumptions
    assert model.confidence_summary.limitations or model.coverage_summary.limitations


def test_repository_references_preserve_ids_without_enrichment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stack, portfolio_id, details, service = _build_presentation_stack(monkeypatch)
    # Mixed portfolio for richer affected-repo sets.
    other = _seed_repository(stack, idx=2, tech_key="podman")
    from codestrata_platform.application.portfolio.commands import (
        AddRepositoryToPortfolioCommand,
        RebuildPortfolioSnapshotCommand,
    )

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
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    model = service.get(
        GetExecutivePresentationQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(
                details.summary.executive_intelligence_id
            ),
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    for ref in model.repository_references:
        assert ref.repository_id
        assert ref.display_name is None
        assert ref.snapshot_id is None
        assert ref.status is None
        assert ref.participation_state is None


def test_latest_and_portfolio_snapshot_lookups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stack, portfolio_id, details, service = _build_presentation_stack(monkeypatch)
    latest = service.get_latest(
        GetLatestExecutivePresentationQuery(
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
        GetExecutivePresentationByPortfolioSnapshotQuery(
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


def test_tenant_mismatch_and_missing_presentation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stack, _, details, service = _build_presentation_stack(monkeypatch)
    from codestrata_platform.application.executive_intelligence.errors import (
        ExecutiveIntelligenceNotFoundError,
    )
    from codestrata_platform.domain.workspace.ids import WorkspaceId

    with pytest.raises(ExecutiveIntelligenceNotFoundError):
        service.get(
            GetExecutivePresentationQuery(
                executive_intelligence_id=ExecutiveIntelligenceId(
                    details.summary.executive_intelligence_id
                ),
                organization_id=stack["org"].organization_id,
                workspace_id=WorkspaceId("workspace:other"),
            )
        )
    with pytest.raises(ExecutivePresentationNotFoundError):
        service.get_by_portfolio_snapshot(
            GetExecutivePresentationByPortfolioSnapshotQuery(
                portfolio_snapshot_id=PortfolioSnapshotId("portfolio-snapshot:missing"),
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )
