"""Deterministic Strategic Portfolio Roadmap builder.

Consumes completed Executive Intelligence only. Does not recalculate EI metrics,
access Portfolio Intelligence/CEIM/KG, or invoke an LLM.
"""

from __future__ import annotations

from collections import Counter

from codestrata_platform.application.executive_intelligence.models import (
    ExecutiveIntelligenceDetails,
)
from codestrata_platform.application.strategic_roadmap.models import (
    STRATEGIC_ROADMAP_POLICY_VERSION,
    STRATEGIC_ROADMAP_SCHEMA_VERSION,
    RoadmapEffortBand,
    RoadmapIdentity,
    RoadmapInitiative,
    RoadmapInitiativeCategory,
    RoadmapSummary,
    RoadmapWave,
    RoadmapWaveBucket,
    StrategicRoadmapModel,
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

_THEME_TO_CATEGORY: dict[ExecutiveRecommendationTheme, RoadmapInitiativeCategory] = {
    ExecutiveRecommendationTheme.MODERNIZATION: RoadmapInitiativeCategory.MODERNIZATION,
    ExecutiveRecommendationTheme.STANDARDIZATION: RoadmapInitiativeCategory.STANDARDIZATION,
    ExecutiveRecommendationTheme.ENGINEERING_INVESTMENT: (
        RoadmapInitiativeCategory.TECHNICAL_DEBT
    ),
    ExecutiveRecommendationTheme.ARCHITECTURE_IMPROVEMENT: (
        RoadmapInitiativeCategory.ARCHITECTURE
    ),
    ExecutiveRecommendationTheme.PLATFORM_ENGINEERING: (
        RoadmapInitiativeCategory.PLATFORM_ENGINEERING
    ),
    ExecutiveRecommendationTheme.GOVERNANCE: RoadmapInitiativeCategory.GOVERNANCE,
    ExecutiveRecommendationTheme.CLOUD_STRATEGY: RoadmapInitiativeCategory.CLOUD,
    ExecutiveRecommendationTheme.AI_ADOPTION: RoadmapInitiativeCategory.AI_ADOPTION,
}

_WAVE_TITLES: dict[RoadmapWave, tuple[str, str]] = {
    RoadmapWave.WAVE_1: (
        "Wave 1 — Urgent value",
        "Highest-value, urgent-risk initiatives with manageable effort.",
    ),
    RoadmapWave.WAVE_2: (
        "Wave 2 — Foundational improvements",
        "Foundational engineering and governance improvements.",
    ),
    RoadmapWave.WAVE_3: (
        "Wave 3 — Strategic modernization",
        "Broader modernization and platform initiatives.",
    ),
    RoadmapWave.WAVE_4: (
        "Wave 4 — Long-term optimization",
        "Longer-horizon optimization and lower-urgency work.",
    ),
}

_SEVERITY_BOOST: dict[ExecutiveImpactBand, int] = {
    ExecutiveImpactBand.CRITICAL: 15,
    ExecutiveImpactBand.HIGH: 10,
    ExecutiveImpactBand.MEDIUM: 5,
    ExecutiveImpactBand.LOW: 0,
}


def _clamp(value: int) -> int:
    return max(0, min(100, int(value)))


def _metric_map(details: ExecutiveIntelligenceDetails) -> dict[ExecutiveMetricKey, ExecutiveMetric]:
    return {item.key: item for item in details.metrics}


def _metric_score(
    metrics: dict[ExecutiveMetricKey, ExecutiveMetric],
    key: ExecutiveMetricKey,
    default: int = 0,
) -> int:
    item = metrics.get(key)
    return item.score if item is not None else default


def _initiative_coverage(
    recommendation: ExecutiveRecommendation,
    metrics: dict[ExecutiveMetricKey, ExecutiveMetric],
) -> float:
    """Propagate related Executive metric coverage without inventing full coverage."""

    metric_keys = {
        ExecutiveRecommendationTheme.MODERNIZATION: ExecutiveMetricKey.MODERNIZATION_READINESS,
        ExecutiveRecommendationTheme.STANDARDIZATION: (
            ExecutiveMetricKey.TECHNOLOGY_STANDARDIZATION
        ),
        ExecutiveRecommendationTheme.ENGINEERING_INVESTMENT: (
            ExecutiveMetricKey.TECHNICAL_DEBT_INDEX
        ),
        ExecutiveRecommendationTheme.ARCHITECTURE_IMPROVEMENT: (
            ExecutiveMetricKey.ARCHITECTURE_MATURITY
        ),
        ExecutiveRecommendationTheme.CLOUD_STRATEGY: ExecutiveMetricKey.CLOUD_ADOPTION,
        ExecutiveRecommendationTheme.AI_ADOPTION: ExecutiveMetricKey.AI_READINESS,
        ExecutiveRecommendationTheme.GOVERNANCE: ExecutiveMetricKey.ASSESSMENT_COVERAGE,
        ExecutiveRecommendationTheme.PLATFORM_ENGINEERING: ExecutiveMetricKey.DEPENDENCY_HEALTH,
    }
    metric_key = metric_keys.get(recommendation.theme)
    if metric_key is None:
        return 0.0
    related_metric = metrics.get(metric_key)
    if related_metric is None:
        return 0.0
    return related_metric.coverage


def _priority_for_recommendation(
    recommendation: ExecutiveRecommendation,
    metrics: dict[ExecutiveMetricKey, ExecutiveMetric],
) -> tuple[int, tuple[str, ...]]:
    risk = _metric_score(metrics, ExecutiveMetricKey.PORTFOLIO_RISK)
    health = _metric_score(metrics, ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH, 100)
    debt = _metric_score(metrics, ExecutiveMetricKey.TECHNICAL_DEBT_INDEX)
    security = _metric_score(metrics, ExecutiveMetricKey.SECURITY_POSTURE, 100)
    dependency = _metric_score(metrics, ExecutiveMetricKey.DEPENDENCY_HEALTH, 100)
    standardization = _metric_score(
        metrics, ExecutiveMetricKey.TECHNOLOGY_STANDARDIZATION, 100
    )
    architecture = _metric_score(metrics, ExecutiveMetricKey.ARCHITECTURE_MATURITY, 100)
    modernization = _metric_score(
        metrics, ExecutiveMetricKey.MODERNIZATION_READINESS, 100
    )

    base = recommendation.priority_score
    theme_boost = 0
    inputs = [
        f"recommendation.priority_score:{recommendation.priority_score}",
        f"portfolio_risk:{risk}",
        f"overall_engineering_health:{health}",
    ]
    if recommendation.theme is ExecutiveRecommendationTheme.ENGINEERING_INVESTMENT:
        theme_boost = max(0, debt // 5)
        inputs.append(f"technical_debt_index:{debt}")
    elif recommendation.theme is ExecutiveRecommendationTheme.STANDARDIZATION:
        theme_boost = max(0, (100 - standardization) // 5)
        inputs.append(f"technology_standardization:{standardization}")
    elif recommendation.theme is ExecutiveRecommendationTheme.ARCHITECTURE_IMPROVEMENT:
        theme_boost = max(0, (100 - architecture) // 5)
        inputs.append(f"architecture_maturity:{architecture}")
    elif recommendation.theme is ExecutiveRecommendationTheme.CLOUD_STRATEGY:
        cloud = _metric_score(metrics, ExecutiveMetricKey.CLOUD_ADOPTION, 100)
        # Heuristic cloud signals get a dampened boost.
        theme_boost = max(0, (100 - cloud) // 10)
        inputs.append(f"cloud_adoption:{cloud}")
    elif recommendation.theme is ExecutiveRecommendationTheme.AI_ADOPTION:
        ai = _metric_score(metrics, ExecutiveMetricKey.AI_READINESS)
        # Heuristic AI-readiness tagging gets a dampened boost.
        theme_boost = max(0, (100 - ai) // 10)
        inputs.append(f"ai_readiness:{ai}")
    elif recommendation.theme is ExecutiveRecommendationTheme.PLATFORM_ENGINEERING:
        theme_boost = max(0, (100 - dependency) // 5)
        inputs.append(f"dependency_health:{dependency}")
    elif recommendation.theme is ExecutiveRecommendationTheme.MODERNIZATION:
        theme_boost = max(0, (100 - modernization) // 10)
        inputs.append(f"modernization_readiness:{modernization}")
    elif recommendation.theme is ExecutiveRecommendationTheme.GOVERNANCE:
        theme_boost = max(0, (100 - health) // 5)
        inputs.append(f"security_posture:{security}")

    risk_boost = risk // 10
    priority = _clamp(base + theme_boost + risk_boost)

    # Weak/heuristic cloud and AI evidence must not create Wave-1 urgency.
    if recommendation.theme in {
        ExecutiveRecommendationTheme.AI_ADOPTION,
        ExecutiveRecommendationTheme.CLOUD_STRATEGY,
    }:
        related_key = (
            ExecutiveMetricKey.AI_READINESS
            if recommendation.theme is ExecutiveRecommendationTheme.AI_ADOPTION
            else ExecutiveMetricKey.CLOUD_ADOPTION
        )
        related = metrics.get(related_key)
        if related is None or related.confidence_band is not ExecutiveConfidenceBand.HIGH:
            priority = min(priority, 65)
            inputs.append("heuristic_theme_priority_cap:65")

    inputs.extend(
        [
            f"theme_boost:{theme_boost}",
            f"risk_boost:{risk_boost}",
            f"priority:{priority}",
        ]
    )
    return priority, tuple(inputs)


def _effort_band(
    recommendation: ExecutiveRecommendation,
) -> tuple[RoadmapEffortBand, str]:
    repo_count = len(set(recommendation.affected_repository_ids))
    impact = recommendation.expected_impact

    if (
        recommendation.theme
        in {
            ExecutiveRecommendationTheme.AI_ADOPTION,
            ExecutiveRecommendationTheme.CLOUD_STRATEGY,
            ExecutiveRecommendationTheme.PLATFORM_ENGINEERING,
        }
        and (repo_count >= 3 or impact in {ExecutiveImpactBand.HIGH, ExecutiveImpactBand.CRITICAL})
    ):
        return (
            RoadmapEffortBand.STRATEGIC,
            "Strategic themes with broad repository/impact scope map to Strategic effort.",
        )
    if repo_count >= 8 or (
        impact is ExecutiveImpactBand.CRITICAL and repo_count >= 4
    ):
        return (
            RoadmapEffortBand.STRATEGIC,
            ">=8 affected repositories or critical impact across >=4 repositories → Strategic.",
        )
    if repo_count >= 4 or impact is ExecutiveImpactBand.HIGH:
        return (
            RoadmapEffortBand.LARGE,
            ">=4 affected repositories or high impact → Large.",
        )
    if repo_count >= 2 or impact is ExecutiveImpactBand.MEDIUM:
        return (
            RoadmapEffortBand.MEDIUM,
            "2-3 affected repositories or medium impact → Medium.",
        )
    return (
        RoadmapEffortBand.SMALL,
        "<=1 affected repository with low/medium bounded scope → Small.",
    )


def _wave_for(
    priority: int,
    effort: RoadmapEffortBand,
) -> tuple[RoadmapWave, str]:
    if priority >= 70 and effort in {RoadmapEffortBand.SMALL, RoadmapEffortBand.MEDIUM}:
        return (
            RoadmapWave.WAVE_1,
            "priority>=70 and effort in {small,medium} → Wave 1 (urgent value).",
        )
    if priority >= 70 and effort in {RoadmapEffortBand.LARGE, RoadmapEffortBand.STRATEGIC}:
        return (
            RoadmapWave.WAVE_2,
            "priority>=70 with large/strategic effort → Wave 2 (foundational).",
        )
    if priority >= 55:
        return (
            RoadmapWave.WAVE_2,
            "priority>=55 → Wave 2 (foundational improvements).",
        )
    if priority >= 30:
        return (
            RoadmapWave.WAVE_3,
            "priority>=30 → Wave 3 (strategic modernization).",
        )
    return (
        RoadmapWave.WAVE_4,
        "priority<30 → Wave 4 (long-term optimization).",
    )


def _limitations_for(
    recommendation: ExecutiveRecommendation,
    coverage: float,
    details_limitations: tuple[str, ...],
) -> tuple[str, ...]:
    items: list[str] = list(details_limitations)
    if recommendation.confidence_band is ExecutiveConfidenceBand.LOW:
        items.append(
            "Initiative confidence is low; validate before committing engineering capacity."
        )
    if coverage < 1.0:
        items.append(
            f"Initiative coverage is {coverage:.2f}; incomplete Executive metric coverage "
            "limits planning certainty."
        )
    return tuple(dict.fromkeys(items))


def _build_initiative(
    recommendation: ExecutiveRecommendation,
    metrics: dict[ExecutiveMetricKey, ExecutiveMetric],
    details_limitations: tuple[str, ...],
) -> RoadmapInitiative:
    priority, priority_inputs = _priority_for_recommendation(recommendation, metrics)
    effort, effort_rule = _effort_band(recommendation)
    wave, wave_rule = _wave_for(priority, effort)
    coverage = _initiative_coverage(recommendation, metrics)
    category = _THEME_TO_CATEGORY[recommendation.theme]
    return RoadmapInitiative(
        initiative_id=f"roadmap-init:{recommendation.recommendation_id.value}",
        title=recommendation.title,
        category=category,
        description=recommendation.rationale,
        rationale=recommendation.rationale,
        affected_repository_ids=recommendation.affected_repository_ids,
        supporting_finding_ids=(),  # EI recommendations do not expose finding links
        supporting_recommendation_ids=(recommendation.recommendation_id.value,),
        expected_impact=recommendation.expected_impact.value,
        confidence=recommendation.confidence,
        confidence_band=recommendation.confidence_band.value,
        coverage=coverage,
        limitations=_limitations_for(recommendation, coverage, details_limitations),
        priority=priority,
        effort_band=effort,
        sequencing_wave=wave,
        related_initiative_ids=(),  # filled after all initiatives exist
        depends_on_initiative_ids=(),  # EI does not evidence implementation dependencies
        priority_inputs=priority_inputs,
        effort_rule=effort_rule,
        wave_rule=wave_rule,
    )


def _related_by_shared_repositories(
    initiatives: tuple[RoadmapInitiative, ...],
) -> tuple[RoadmapInitiative, ...]:
    """Attach evidence-backed related IDs from shared affected repositories only."""

    repo_to_initiatives: dict[str, list[str]] = {}
    order = {item.initiative_id: index for index, item in enumerate(initiatives)}
    for item in initiatives:
        for repo_id in item.affected_repository_ids:
            repo_to_initiatives.setdefault(repo_id, []).append(item.initiative_id)

    related_by_id: dict[str, tuple[str, ...]] = {}
    for item in initiatives:
        related: set[str] = set()
        for repo_id in item.affected_repository_ids:
            related.update(repo_to_initiatives.get(repo_id, ()))
        related.discard(item.initiative_id)
        related_by_id[item.initiative_id] = tuple(
            sorted(related, key=lambda initiative_id: order[initiative_id])
        )

    updated: list[RoadmapInitiative] = []
    for item in initiatives:
        updated.append(
            RoadmapInitiative(
                initiative_id=item.initiative_id,
                title=item.title,
                category=item.category,
                description=item.description,
                rationale=item.rationale,
                affected_repository_ids=item.affected_repository_ids,
                supporting_finding_ids=item.supporting_finding_ids,
                supporting_recommendation_ids=item.supporting_recommendation_ids,
                expected_impact=item.expected_impact,
                confidence=item.confidence,
                confidence_band=item.confidence_band,
                coverage=item.coverage,
                limitations=item.limitations,
                priority=item.priority,
                effort_band=item.effort_band,
                sequencing_wave=item.sequencing_wave,
                related_initiative_ids=related_by_id[item.initiative_id],
                depends_on_initiative_ids=(),
                priority_inputs=item.priority_inputs,
                effort_rule=item.effort_rule,
                wave_rule=item.wave_rule,
            )
        )
    return tuple(updated)


def _wave_buckets(initiatives: tuple[RoadmapInitiative, ...]) -> tuple[RoadmapWaveBucket, ...]:
    buckets: list[RoadmapWaveBucket] = []
    for wave in RoadmapWave:
        ids = tuple(
            item.initiative_id
            for item in initiatives
            if item.sequencing_wave is wave
        )
        title, description = _WAVE_TITLES[wave]
        buckets.append(
            RoadmapWaveBucket(
                wave=wave,
                title=title,
                description=description,
                initiative_ids=ids,
                initiative_count=len(ids),
            )
        )
    return tuple(buckets)


def _distribution(counter: Counter[str]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(counter.items(), key=lambda item: item[0]))


def _summary(
    initiatives: tuple[RoadmapInitiative, ...],
    observations: tuple[StrategicObservation, ...],
    limitations: tuple[str, ...],
) -> RoadmapSummary:
    effort = Counter(item.effort_band.value for item in initiatives)
    waves = Counter(item.sequencing_wave.value for item in initiatives)
    categories = Counter(item.category.value for item in initiatives)
    themes = tuple(
        dict.fromkeys(
            item.category.value
            for item in sorted(initiatives, key=lambda init: (-init.priority, init.initiative_id))
        )
    )
    strategic_observations = tuple(
        f"{item.title}: {item.summary}" for item in observations
    )
    return RoadmapSummary(
        initiative_count=len(initiatives),
        effort_distribution=_distribution(effort),
        wave_distribution=_distribution(waves),
        category_distribution=_distribution(categories),
        portfolio_investment_themes=themes,
        strategic_observations=strategic_observations,
        limitations=limitations,
    )


def _build_finding_initiative(
    finding: ExecutiveFinding,
    metrics: dict[ExecutiveMetricKey, ExecutiveMetric],
    details_limitations: tuple[str, ...],
) -> RoadmapInitiative:
    category = {
        ExecutiveFindingCategory.SECURITY_HOTSPOT: RoadmapInitiativeCategory.SECURITY,
        ExecutiveFindingCategory.DEPENDENCY_HOTSPOT: RoadmapInitiativeCategory.DEPENDENCY,
        ExecutiveFindingCategory.TECHNICAL_DEBT_CONCENTRATION: (
            RoadmapInitiativeCategory.TECHNICAL_DEBT
        ),
    }[finding.category]
    risk = _metric_score(metrics, ExecutiveMetricKey.PORTFOLIO_RISK)
    priority = _clamp(
        _SEVERITY_BOOST[finding.severity_band] * 5
        + risk // 5
        + len(finding.affected_repository_ids) * 5
    )
    repo_count = len(set(finding.affected_repository_ids))
    impact = finding.severity_band
    if repo_count >= 8 or (impact is ExecutiveImpactBand.CRITICAL and repo_count >= 4):
        effort, effort_rule = (
            RoadmapEffortBand.STRATEGIC,
            ">=8 affected repositories or critical impact across >=4 repositories → Strategic.",
        )
    elif repo_count >= 4 or impact is ExecutiveImpactBand.HIGH:
        effort, effort_rule = (
            RoadmapEffortBand.LARGE,
            ">=4 affected repositories or high impact → Large.",
        )
    elif repo_count >= 2 or impact is ExecutiveImpactBand.MEDIUM:
        effort, effort_rule = (
            RoadmapEffortBand.MEDIUM,
            "2-3 affected repositories or medium impact → Medium.",
        )
    else:
        effort, effort_rule = (
            RoadmapEffortBand.SMALL,
            "<=1 affected repository with low/medium bounded scope → Small.",
        )
    wave, wave_rule = _wave_for(priority, effort)
    coverage_key = {
        RoadmapInitiativeCategory.SECURITY: ExecutiveMetricKey.SECURITY_POSTURE,
        RoadmapInitiativeCategory.DEPENDENCY: ExecutiveMetricKey.DEPENDENCY_HEALTH,
        RoadmapInitiativeCategory.TECHNICAL_DEBT: ExecutiveMetricKey.TECHNICAL_DEBT_INDEX,
    }[category]
    related_metric = metrics.get(coverage_key)
    coverage = related_metric.coverage if related_metric is not None else 0.0
    limitations = list(details_limitations)
    if finding.confidence_band is ExecutiveConfidenceBand.LOW:
        limitations.append(
            "Initiative confidence is low; validate before committing engineering capacity."
        )
    if coverage < 1.0:
        limitations.append(
            f"Initiative coverage is {coverage:.2f}; incomplete Executive metric coverage "
            "limits planning certainty."
        )
    return RoadmapInitiative(
        initiative_id=f"roadmap-init:{finding.finding_id.value}",
        title=finding.title,
        category=category,
        description=finding.summary,
        rationale=finding.summary,
        affected_repository_ids=finding.affected_repository_ids,
        supporting_finding_ids=(finding.finding_id.value,),
        supporting_recommendation_ids=(),
        expected_impact=finding.severity_band.value,
        confidence=finding.confidence,
        confidence_band=finding.confidence_band.value,
        coverage=coverage,
        limitations=tuple(dict.fromkeys(limitations)),
        priority=priority,
        effort_band=effort,
        sequencing_wave=wave,
        related_initiative_ids=(),
        depends_on_initiative_ids=(),
        priority_inputs=(
            f"finding.severity_band:{finding.severity_band.value}",
            f"portfolio_risk:{risk}",
            f"priority:{priority}",
        ),
        effort_rule=effort_rule,
        wave_rule=wave_rule,
    )


def build_strategic_roadmap(
    details: ExecutiveIntelligenceDetails,
) -> StrategicRoadmapModel:
    """Project a completed Executive Intelligence snapshot into a strategic roadmap."""

    if details.summary.status is not ExecutiveIntelligenceStatus.COMPLETED:
        raise ValueError(
            "Strategic Roadmap requires a completed Executive Intelligence snapshot"
        )

    metrics = _metric_map(details)
    draft = [
        _build_initiative(
            recommendation,
            metrics,
            details.limitations,
        )
        for recommendation in details.recommendations
    ]
    # HIGH/CRITICAL security, dependency, and technical-debt findings become
    # finding-backed initiatives; EI recommendations do not invent finding coverage.
    for finding in details.findings:
        if finding.severity_band not in {
            ExecutiveImpactBand.HIGH,
            ExecutiveImpactBand.CRITICAL,
        }:
            continue
        if finding.category not in {
            ExecutiveFindingCategory.SECURITY_HOTSPOT,
            ExecutiveFindingCategory.DEPENDENCY_HOTSPOT,
            ExecutiveFindingCategory.TECHNICAL_DEBT_CONCENTRATION,
        }:
            continue
        draft.append(
            _build_finding_initiative(finding, metrics, details.limitations)
        )

    ordered = tuple(
        sorted(draft, key=lambda item: (-item.priority, item.initiative_id))
    )
    initiatives = _related_by_shared_repositories(ordered)
    waves = _wave_buckets(initiatives)
    identity = RoadmapIdentity(
        executive_intelligence_id=details.summary.executive_intelligence_id,
        organization_id=details.summary.organization_id,
        workspace_id=details.summary.workspace_id,
        portfolio_id=details.summary.portfolio_id,
        portfolio_snapshot_id=details.summary.portfolio_snapshot_id,
        portfolio_snapshot_version=details.summary.portfolio_snapshot_version,
        executive_version=details.summary.version,
        projection_completed_at=details.summary.completed_at,
        schema_version=STRATEGIC_ROADMAP_SCHEMA_VERSION,
        policy_version=STRATEGIC_ROADMAP_POLICY_VERSION,
        source_policy_version=details.summary.policy_version,
        source_schema_version=details.summary.schema_version,
    )
    return StrategicRoadmapModel(
        identity=identity,
        summary=_summary(initiatives, details.observations, details.limitations),
        initiatives=initiatives,
        waves=waves,
        limitations=details.limitations,
    )


class StrategicRoadmapBuilder:
    """Single boundary from Executive Intelligence to roadmap models."""

    def build(self, details: ExecutiveIntelligenceDetails) -> StrategicRoadmapModel:
        return build_strategic_roadmap(details)
