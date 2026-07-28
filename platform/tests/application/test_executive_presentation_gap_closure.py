"""Regression coverage for Executive Presentation audit gap closure."""

from __future__ import annotations

import pytest

from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_presentation.adapter import (
    ExecutivePresentationAdapter,
)
from codestrata_platform.application.executive_presentation.queries import (
    GetExecutivePresentationQuery,
)
from codestrata_platform.application.executive_presentation.services import (
    ExecutivePresentationService,
)
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveConfidenceBand,
    ExecutiveFindingCategory,
    ExecutiveMetricKey,
)

from .test_executive_intelligence_service import (
    _build_portfolio,
    _enable_executive_intelligence,
    _seed_repository,
    _stack,
)
from .test_executive_presentation import _enable_presentation


def _presentation_for_repos(monkeypatch: pytest.MonkeyPatch, *, count: int = 4):
    _enable_executive_intelligence(monkeypatch)
    _enable_presentation(monkeypatch)
    stack = _stack()
    repos = [_seed_repository(stack, idx=i, tech_key=f"tech-{i}") for i in range(1, count + 1)]
    portfolio_id = _build_portfolio(stack, repo_ids=repos)
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
        )
    )
    return stack, details, model


def test_recommendations_do_not_invent_supporting_finding_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, details, model = _presentation_for_repos(monkeypatch)
    assert details.recommendations
    for recommendation in model.recommendations:
        assert recommendation.supporting_finding_ids == ()


def test_repository_references_preserve_first_seen_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, details, model = _presentation_for_repos(monkeypatch)
    expected: list[str] = []
    seen: set[str] = set()
    for finding in details.findings:
        for repo_id in finding.affected_repository_ids:
            if repo_id not in seen:
                seen.add(repo_id)
                expected.append(repo_id)
    for recommendation in details.recommendations:
        for repo_id in recommendation.affected_repository_ids:
            if repo_id not in seen:
                seen.add(repo_id)
                expected.append(repo_id)
    assert [item.repository_id for item in model.repository_references] == expected


def test_confidence_and_coverage_limitations_match_executive_exactly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, details, model = _presentation_for_repos(monkeypatch)
    assert model.confidence_summary.limitations == details.limitations
    assert model.coverage_summary.limitations == details.limitations
    assert model.limitations_and_assumptions == details.limitations
    assert "One or more metrics report incomplete coverage." not in (
        model.coverage_summary.limitations
    )


def test_executive_summary_excludes_low_confidence_strengths_weaknesses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, details, model = _presentation_for_repos(monkeypatch)
    low_titles = {
        item.title
        for item in details.findings
        if item.category
        in {
            ExecutiveFindingCategory.PORTFOLIO_STRENGTH,
            ExecutiveFindingCategory.PORTFOLIO_WEAKNESS,
        }
        and item.confidence_band is ExecutiveConfidenceBand.LOW
    }
    for title in model.executive_summary.major_strengths:
        assert title not in low_titles
    for title in model.executive_summary.major_weaknesses:
        assert title not in low_titles
    for item in model.engineering_strengths:
        if not item.definitive:
            assert item.title not in model.executive_summary.major_strengths
    for item in model.engineering_weaknesses:
        if not item.definitive:
            assert item.title not in model.executive_summary.major_weaknesses


def test_low_confidence_metrics_do_not_overstate_summary_language(
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
    # Empty portfolio metrics are low confidence; presentation must caveat language.
    model = ExecutivePresentationAdapter().adapt(details)
    health = next(
        item
        for item in details.metrics
        if item.key is ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH
    )
    assert health.confidence_band is ExecutiveConfidenceBand.LOW
    assert "provisional" in model.executive_summary.headline.lower()
    assert "provisional" in model.executive_summary.confidence_statement.lower()
    assert "provisional" in model.executive_summary.modernization_outlook.lower()


def test_technology_landscape_projects_executive_findings_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, details, model = _presentation_for_repos(monkeypatch)
    frag_ids = {
        item.finding_id.value
        for item in details.findings
        if item.category is ExecutiveFindingCategory.TECHNOLOGY_FRAGMENTATION
    }
    dup_ids = {
        item.finding_id.value
        for item in details.findings
        if item.category is ExecutiveFindingCategory.DUPLICATED_TECHNOLOGY_STACK
    }
    unsupported_ids = {
        item.finding_id.value
        for item in details.findings
        if item.category is ExecutiveFindingCategory.UNSUPPORTED_TECHNOLOGY
    }
    assert {item.key for item in model.technology_landscape.fragmentation} == frag_ids
    assert {item.key for item in model.technology_landscape.duplicated_stacks} == dup_ids
    assert {
        item.key for item in model.technology_landscape.unsupported_technologies
    } == unsupported_ids


def test_codestrata_dogfood_presentation_is_traceable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dogfood presentation for a CodeStrata-shaped portfolio (CTO/CIO readability)."""

    _, details, model = _presentation_for_repos(monkeypatch, count=4)
    assert model.identity.executive_intelligence_id == details.summary.executive_intelligence_id
    assert model.executive_summary.headline
    assert model.cto_summary.engineering_health.score == next(
        item.score
        for item in details.metrics
        if item.key is ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH
    )
    assert all(
        card.score
        == next(item.score for item in details.metrics if item.key is card.metric_key)
        for card in model.kpi_cards
    )
    assert model.limitations_and_assumptions == details.limitations
    assert all(point.direction.value == "unknown" for point in model.trend_ready_metrics)
    assert model.confidence_summary.limitations == details.limitations
