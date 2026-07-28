"""Regression coverage for Strategic Portfolio Roadmap audit gap closure."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_intelligence.models import (
    ExecutiveIntelligenceDetails,
    ExecutiveIntelligenceSummary,
)
from codestrata_platform.application.strategic_roadmap.builder import (
    StrategicRoadmapBuilder,
)
from codestrata_platform.application.strategic_roadmap.models import (
    RoadmapEffortBand,
    RoadmapInitiativeCategory,
    RoadmapWave,
)
from codestrata_platform.domain.engineering.enums import EngineeringCategory
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveFindingId,
    ExecutiveMetricId,
    ExecutiveRecommendationId,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveConfidenceBand,
    ExecutiveFindingCategory,
    ExecutiveImpactBand,
    ExecutiveIntelligenceStatus,
    ExecutiveMetricKey,
    ExecutiveRecommendationTheme,
)
from codestrata_platform.domain.executive_intelligence.models import (
    ExecutiveFinding,
    ExecutiveMetric,
    ExecutiveRecommendation,
    StrategicObservation,
)

from .test_executive_intelligence_service import (
    _build_portfolio,
    _enable_executive_intelligence,
    _seed_repository,
    _stack,
)
from .test_strategic_roadmap import _enable_roadmap


def _summary(**overrides: object) -> ExecutiveIntelligenceSummary:
    base = {
        "executive_intelligence_id": "exec:1",
        "organization_id": "org:1",
        "workspace_id": "workspace:1",
        "portfolio_id": "portfolio:1",
        "portfolio_snapshot_id": "portfolio-snapshot:1",
        "portfolio_snapshot_version": 1,
        "version": 1,
        "status": ExecutiveIntelligenceStatus.COMPLETED,
        "projection_key": "projection:1",
        "schema_version": "executive-schema-v1",
        "policy_version": "executive-aggregation-v1",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "updated_at": datetime(2026, 1, 1, tzinfo=UTC),
        "completed_at": datetime(2026, 1, 1, tzinfo=UTC),
        "superseded_at": None,
        "failure_reason": None,
        "metric_count": 0,
        "finding_count": 0,
        "recommendation_count": 0,
        "observation_count": 0,
    }
    base.update(overrides)
    return ExecutiveIntelligenceSummary(**base)  # type: ignore[arg-type]


def _metric(
    key: ExecutiveMetricKey,
    *,
    score: int = 50,
    confidence: float = 0.5,
    confidence_band: ExecutiveConfidenceBand = ExecutiveConfidenceBand.MEDIUM,
    coverage: float = 0.4,
) -> ExecutiveMetric:
    return ExecutiveMetric(
        metric_id=ExecutiveMetricId.for_metric("exec:1", key.value),
        key=key,
        score=score,
        confidence=confidence,
        confidence_band=confidence_band,
        coverage=coverage,
        inputs=("test",),
        calculation_rule="test rule",
        limitations=(),
        policy_version="executive-aggregation-v1",
    )


def _recommendation(
    *,
    key: str,
    theme: ExecutiveRecommendationTheme,
    priority_score: int = 100,
    impact: ExecutiveImpactBand = ExecutiveImpactBand.HIGH,
    repos: tuple[str, ...] = ("repo:engine",),
    confidence: float = 0.7,
    confidence_band: ExecutiveConfidenceBand = ExecutiveConfidenceBand.MEDIUM,
) -> ExecutiveRecommendation:
    return ExecutiveRecommendation(
        recommendation_id=ExecutiveRecommendationId.for_recommendation("exec:1", key),
        theme=theme,
        title=f"{theme.value} initiative",
        rationale=f"Rationale for {theme.value}",
        affected_repository_ids=repos,
        confidence=confidence,
        confidence_band=confidence_band,
        expected_impact=impact,
        source_references=("portfolio-snapshot:1",),
        priority_score=priority_score,
        policy_version="executive-aggregation-v1",
    )


def _finding(
    *,
    key: str,
    category: ExecutiveFindingCategory,
    severity: ExecutiveImpactBand = ExecutiveImpactBand.HIGH,
    repos: tuple[str, ...] = ("repo:engine",),
) -> ExecutiveFinding:
    return ExecutiveFinding(
        finding_id=ExecutiveFindingId.for_finding("exec:1", key),
        category=category,
        title=f"{category.value} finding",
        summary=f"Summary for {category.value}",
        severity_band=severity,
        confidence=0.8,
        confidence_band=ExecutiveConfidenceBand.HIGH,
        affected_repository_ids=repos,
        source_references=("portfolio-snapshot:1",),
        evidence=("evidence",),
        policy_version="executive-aggregation-v1",
    )


def test_recommendation_initiatives_do_not_invent_supporting_finding_ids() -> None:
    finding = _finding(
        key="security",
        category=ExecutiveFindingCategory.SECURITY_HOTSPOT,
        repos=("repo:engine",),
    )
    recommendation = _recommendation(
        key="modernize",
        theme=ExecutiveRecommendationTheme.MODERNIZATION,
        repos=("repo:engine",),
    )
    details = ExecutiveIntelligenceDetails(
        summary=_summary(finding_count=1, recommendation_count=1, metric_count=1),
        metrics=(_metric(ExecutiveMetricKey.MODERNIZATION_READINESS, coverage=0.3),),
        findings=(finding,),
        recommendations=(recommendation,),
        observations=(),
        limitations=("EI limitation",),
    )
    model = StrategicRoadmapBuilder().build(details)
    rec_initiatives = [
        item
        for item in model.initiatives
        if item.supporting_recommendation_ids
    ]
    assert rec_initiatives
    for initiative in rec_initiatives:
        assert initiative.supporting_finding_ids == ()


def test_empty_roadmap_does_not_invent_summary_observations() -> None:
    details = ExecutiveIntelligenceDetails(
        summary=_summary(metric_count=1),
        metrics=(_metric(ExecutiveMetricKey.PORTFOLIO_RISK),),
        findings=(),
        recommendations=(),
        observations=(),
        limitations=("empty portfolio",),
    )
    model = StrategicRoadmapBuilder().build(details)
    assert model.initiatives == ()
    assert model.summary.strategic_observations == ()
    assert model.summary.initiative_count == 0
    assert model.limitations == details.limitations


def test_summary_observations_are_exact_executive_projections() -> None:
    observation = StrategicObservation(
        observation_key="obs-1",
        title="Coverage gap",
        summary="Participation is incomplete.",
        related_metric_keys=("assessment_coverage",),
        related_finding_ids=(),
        confidence=0.5,
        confidence_band=ExecutiveConfidenceBand.MEDIUM,
    )
    details = ExecutiveIntelligenceDetails(
        summary=_summary(metric_count=1, observation_count=1),
        metrics=(_metric(ExecutiveMetricKey.PORTFOLIO_RISK),),
        findings=(),
        recommendations=(),
        observations=(observation,),
        limitations=("lim",),
    )
    model = StrategicRoadmapBuilder().build(details)
    assert model.summary.strategic_observations == (
        "Coverage gap: Participation is incomplete.",
    )


def test_weak_ai_and_cloud_evidence_cannot_create_wave_1_urgency() -> None:
    ai = _recommendation(
        key="ai",
        theme=ExecutiveRecommendationTheme.AI_ADOPTION,
        priority_score=100,
        impact=ExecutiveImpactBand.MEDIUM,
        repos=("repo:engine",),
    )
    cloud = _recommendation(
        key="cloud",
        theme=ExecutiveRecommendationTheme.CLOUD_STRATEGY,
        priority_score=100,
        impact=ExecutiveImpactBand.MEDIUM,
        repos=("repo:platform",),
    )
    details = ExecutiveIntelligenceDetails(
        summary=_summary(recommendation_count=2, metric_count=3),
        metrics=(
            _metric(ExecutiveMetricKey.PORTFOLIO_RISK, score=80),
            _metric(
                ExecutiveMetricKey.AI_READINESS,
                score=0,
                confidence_band=ExecutiveConfidenceBand.LOW,
                coverage=0.1,
            ),
            _metric(
                ExecutiveMetricKey.CLOUD_ADOPTION,
                score=0,
                confidence_band=ExecutiveConfidenceBand.MEDIUM,
                coverage=0.2,
            ),
        ),
        findings=(),
        recommendations=(ai, cloud),
        observations=(),
        limitations=("AI readiness inferred heuristically",),
    )
    model = StrategicRoadmapBuilder().build(details)
    for initiative in model.initiatives:
        assert initiative.category in {
            RoadmapInitiativeCategory.AI_ADOPTION,
            RoadmapInitiativeCategory.CLOUD,
        }
        assert initiative.priority <= 65
        assert "heuristic_theme_priority_cap:65" in initiative.priority_inputs
        assert initiative.sequencing_wave is not RoadmapWave.WAVE_1


def test_coverage_propagates_metric_coverage_without_inflation() -> None:
    recommendation = _recommendation(
        key="std",
        theme=ExecutiveRecommendationTheme.STANDARDIZATION,
        impact=ExecutiveImpactBand.MEDIUM,
        repos=("repo:a", "repo:b"),
    )
    details = ExecutiveIntelligenceDetails(
        summary=_summary(recommendation_count=1, metric_count=1, finding_count=1),
        metrics=(
            _metric(
                ExecutiveMetricKey.TECHNOLOGY_STANDARDIZATION,
                coverage=0.25,
            ),
        ),
        findings=(
            _finding(
                key="fragmentation",
                category=ExecutiveFindingCategory.TECHNOLOGY_FRAGMENTATION,
                severity=ExecutiveImpactBand.MEDIUM,
                repos=("repo:a",),
            ),
        ),
        recommendations=(recommendation,),
        observations=(),
        limitations=(),
    )
    model = StrategicRoadmapBuilder().build(details)
    initiative = next(
        item
        for item in model.initiatives
        if item.category is RoadmapInitiativeCategory.STANDARDIZATION
    )
    assert initiative.coverage == 0.25
    assert initiative.supporting_finding_ids == ()


def test_depends_on_remains_empty_and_related_is_not_dependency() -> None:
    details = ExecutiveIntelligenceDetails(
        summary=_summary(recommendation_count=2, metric_count=1),
        metrics=(_metric(ExecutiveMetricKey.MODERNIZATION_READINESS),),
        findings=(),
        recommendations=(
            _recommendation(
                key="a",
                theme=ExecutiveRecommendationTheme.MODERNIZATION,
                repos=("repo:shared",),
            ),
            _recommendation(
                key="b",
                theme=ExecutiveRecommendationTheme.GOVERNANCE,
                repos=("repo:shared",),
            ),
        ),
        observations=(),
        limitations=(),
    )
    model = StrategicRoadmapBuilder().build(details)
    assert len(model.initiatives) == 2
    for initiative in model.initiatives:
        assert initiative.depends_on_initiative_ids == ()
        assert initiative.related_initiative_ids
        assert initiative.initiative_id not in initiative.related_initiative_ids


def test_finding_backed_security_and_dependency_initiatives_are_self_traceable() -> None:
    details = ExecutiveIntelligenceDetails(
        summary=_summary(finding_count=2, metric_count=2),
        metrics=(
            _metric(ExecutiveMetricKey.SECURITY_POSTURE, coverage=0.55),
            _metric(ExecutiveMetricKey.DEPENDENCY_HEALTH, coverage=0.4),
            _metric(ExecutiveMetricKey.PORTFOLIO_RISK, score=40),
        ),
        findings=(
            _finding(
                key="sec",
                category=ExecutiveFindingCategory.SECURITY_HOTSPOT,
                severity=ExecutiveImpactBand.CRITICAL,
            ),
            _finding(
                key="dep",
                category=ExecutiveFindingCategory.DEPENDENCY_HOTSPOT,
                severity=ExecutiveImpactBand.HIGH,
            ),
        ),
        recommendations=(),
        observations=(),
        limitations=("security evidence limited",),
    )
    model = StrategicRoadmapBuilder().build(details)
    by_category = {item.category: item for item in model.initiatives}
    assert RoadmapInitiativeCategory.SECURITY in by_category
    assert RoadmapInitiativeCategory.DEPENDENCY in by_category
    security = by_category[RoadmapInitiativeCategory.SECURITY]
    assert security.supporting_finding_ids == (
        ExecutiveFindingId.for_finding("exec:1", "sec").value,
    )
    assert security.supporting_recommendation_ids == ()
    assert security.coverage == 0.55
    assert model.summary.initiative_count == len(model.initiatives)
    wave_total = sum(bucket.initiative_count for bucket in model.waves)
    assert wave_total == model.summary.initiative_count


def test_codestrata_dogfood_portfolio_placeholders_do_not_invent_urgency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    _enable_roadmap(monkeypatch)
    stack = _stack()
    engine = _seed_repository(
        stack, idx=1, tech_key="python", category=EngineeringCategory.ARCHITECTURE
    )
    platform = _seed_repository(
        stack, idx=2, tech_key="fastapi", category=EngineeringCategory.ARCHITECTURE
    )
    # Placeholder-style repos still participate with thin evidence.
    vscode = _seed_repository(
        stack, idx=3, tech_key="typescript", category=EngineeringCategory.OTHER
    )
    cursor = _seed_repository(
        stack, idx=4, tech_key="nodejs", category=EngineeringCategory.OTHER
    )
    docs = _seed_repository(
        stack, idx=5, tech_key="markdown", category=EngineeringCategory.DOCUMENTATION
    )
    portfolio_id = _build_portfolio(
        stack, repo_ids=[engine, platform, vscode, cursor, docs]
    )
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    model = StrategicRoadmapBuilder().build(details)

    assert model.identity.executive_intelligence_id == (
        details.summary.executive_intelligence_id
    )
    assert model.limitations == details.limitations
    assert model.summary.initiative_count == len(model.initiatives)
    assert sum(count for _, count in model.summary.category_distribution) == len(
        model.initiatives
    )
    assert sum(count for _, count in model.summary.wave_distribution) == len(
        model.initiatives
    )
    assert sum(count for _, count in model.summary.effort_distribution) == len(
        model.initiatives
    )

    for initiative in model.initiatives:
        assert initiative.depends_on_initiative_ids == ()
        assert 0 <= initiative.priority <= 100
        assert initiative.effort_band in set(RoadmapEffortBand)
        assert initiative.sequencing_wave in set(RoadmapWave)
        if initiative.supporting_recommendation_ids:
            assert initiative.supporting_finding_ids == ()
        for finding_id in initiative.supporting_finding_ids:
            assert finding_id in {item.finding_id.value for item in details.findings}
        for recommendation_id in initiative.supporting_recommendation_ids:
            assert recommendation_id in {
                item.recommendation_id.value for item in details.recommendations
            }

    for initiative in model.initiatives:
        if initiative.category in {
            RoadmapInitiativeCategory.AI_ADOPTION,
            RoadmapInitiativeCategory.CLOUD,
        }:
            ai_metric = next(
                (
                    item
                    for item in details.metrics
                    if item.key is ExecutiveMetricKey.AI_READINESS
                ),
                None,
            )
            cloud_metric = next(
                (
                    item
                    for item in details.metrics
                    if item.key is ExecutiveMetricKey.CLOUD_ADOPTION
                ),
                None,
            )
            related = (
                ai_metric
                if initiative.category is RoadmapInitiativeCategory.AI_ADOPTION
                else cloud_metric
            )
            if related is None or related.confidence_band is not ExecutiveConfidenceBand.HIGH:
                assert initiative.priority <= 65
                assert initiative.sequencing_wave is not RoadmapWave.WAVE_1
