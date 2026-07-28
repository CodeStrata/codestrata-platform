"""Deterministic Executive Intelligence aggregation over a completed PortfolioSnapshot.

This module MUST consume only the following ``PortfolioSnapshot`` fields:
``risk_summary``, ``modernization_summary``, ``coverage_summary``,
``technology_inventory``, ``dependency_signals``, ``repository_selections``.
It must never import ``EngineeringSnapshot``, CEIM, knowledge graph, retrieval,
or answering concepts — Executive Intelligence is a pure leadership projection
over already-aggregated Portfolio Intelligence.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveFindingId,
    ExecutiveMetricId,
    ExecutiveRecommendationId,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveConfidenceBand,
    ExecutiveFindingCategory,
    ExecutiveImpactBand,
    ExecutiveMetricKey,
    ExecutiveRecommendationTheme,
)
from codestrata_platform.domain.executive_intelligence.models import (
    ExecutiveFinding,
    ExecutiveMetric,
    ExecutiveRecommendation,
    StrategicObservation,
)
from codestrata_platform.domain.portfolio.lifecycle import (
    ModernizationTheme,
    TechnologyLifecycleSignal,
    TechnologyStandardizationStatus,
)
from codestrata_platform.domain.portfolio.snapshot import PortfolioSnapshot
from codestrata_platform.domain.portfolio.technology import PortfolioTechnology

EXECUTIVE_AGGREGATION_POLICY_VERSION = "executive-aggregation-v1"
POLICY_VERSION = EXECUTIVE_AGGREGATION_POLICY_VERSION

_STANDARDIZED_STATUSES = frozenset(
    {TechnologyStandardizationStatus.STANDARD, TechnologyStandardizationStatus.PREFERRED}
)
_EMPTY_PORTFOLIO_LIMITATION = (
    "Portfolio snapshot contains no repositories; scores reflect an empty baseline."
)
_AI_HEURISTIC_LIMITATION = (
    "AI readiness is inferred heuristically from technology category tagging only."
)


@dataclass(frozen=True, slots=True)
class ExecutiveAggregationResult:
    """Deterministic Executive Intelligence aggregation output."""

    metrics: tuple[ExecutiveMetric, ...]
    findings: tuple[ExecutiveFinding, ...]
    recommendations: tuple[ExecutiveRecommendation, ...]
    observations: tuple[StrategicObservation, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Context:
    snapshot_id: str
    technologies: tuple[PortfolioTechnology, ...]
    total_repositories: int
    risk: object | None
    modernization: object | None
    coverage: object | None
    dependencies: object | None

    @property
    def has_repositories(self) -> bool:
        return self.total_repositories > 0


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _confidence_band(confidence: float) -> ExecutiveConfidenceBand:
    if confidence >= 0.75:
        return ExecutiveConfidenceBand.HIGH
    if confidence >= 0.45:
        return ExecutiveConfidenceBand.MEDIUM
    return ExecutiveConfidenceBand.LOW


def _impact_band(score: int) -> ExecutiveImpactBand:
    clamped = max(0, min(100, int(score)))
    if clamped >= 80:
        return ExecutiveImpactBand.CRITICAL
    if clamped >= 55:
        return ExecutiveImpactBand.HIGH
    if clamped >= 25:
        return ExecutiveImpactBand.MEDIUM
    return ExecutiveImpactBand.LOW


def _band_from_value(value: str) -> ExecutiveImpactBand:
    try:
        return ExecutiveImpactBand(value)
    except ValueError:
        return ExecutiveImpactBand.LOW


def _build_context(snapshot: PortfolioSnapshot) -> _Context:
    technologies = tuple(
        item for item in snapshot.technology_inventory if isinstance(item, PortfolioTechnology)
    )
    selections = snapshot.repository_selections
    coverage = snapshot.coverage_summary
    total = int(getattr(coverage, "repositories_total", len(selections)) or len(selections))
    dependencies = snapshot.dependency_signals[0] if snapshot.dependency_signals else None
    return _Context(
        snapshot_id=snapshot.portfolio_snapshot_id.value,
        technologies=technologies,
        total_repositories=total,
        risk=snapshot.risk_summary,
        modernization=snapshot.modernization_summary,
        coverage=coverage,
        dependencies=dependencies,
    )


def _metric(
    ctx: _Context,
    key: ExecutiveMetricKey,
    *,
    score: int,
    confidence: float,
    coverage: float,
    inputs: tuple[str, ...],
    calculation_rule: str,
    limitations: tuple[str, ...] = (),
) -> ExecutiveMetric:
    combined_limitations = limitations
    effective_confidence = confidence
    effective_coverage = coverage
    if not ctx.has_repositories:
        combined_limitations = (*combined_limitations, _EMPTY_PORTFOLIO_LIMITATION)
        effective_confidence = min(confidence, 0.15)
        effective_coverage = 0.0
    return ExecutiveMetric(
        metric_id=ExecutiveMetricId.for_metric(ctx.snapshot_id, key.value),
        key=key,
        score=score if ctx.has_repositories else 0,
        confidence=effective_confidence,
        confidence_band=_confidence_band(effective_confidence),
        coverage=effective_coverage,
        inputs=inputs,
        calculation_rule=calculation_rule,
        limitations=combined_limitations,
        policy_version=EXECUTIVE_AGGREGATION_POLICY_VERSION,
    )


def _finding(
    ctx: _Context,
    *,
    key: str,
    category: ExecutiveFindingCategory,
    title: str,
    summary: str,
    severity_band: ExecutiveImpactBand,
    confidence: float,
    affected_repository_ids: tuple[str, ...],
    evidence: tuple[str, ...],
) -> ExecutiveFinding:
    return ExecutiveFinding(
        finding_id=ExecutiveFindingId.for_finding(ctx.snapshot_id, key),
        category=category,
        title=title,
        summary=summary,
        severity_band=severity_band,
        confidence=confidence,
        confidence_band=_confidence_band(confidence),
        affected_repository_ids=affected_repository_ids,
        source_references=(ctx.snapshot_id,),
        evidence=evidence,
        policy_version=EXECUTIVE_AGGREGATION_POLICY_VERSION,
    )


def _recommendation(
    ctx: _Context,
    *,
    key: str,
    theme: ExecutiveRecommendationTheme,
    title: str,
    rationale: str,
    affected_repository_ids: tuple[str, ...],
    confidence: float,
    expected_impact: ExecutiveImpactBand,
    priority_score: int,
) -> ExecutiveRecommendation:
    return ExecutiveRecommendation(
        recommendation_id=ExecutiveRecommendationId.for_recommendation(ctx.snapshot_id, key),
        theme=theme,
        title=title,
        rationale=rationale,
        affected_repository_ids=affected_repository_ids,
        confidence=confidence,
        confidence_band=_confidence_band(confidence),
        expected_impact=expected_impact,
        source_references=(ctx.snapshot_id,),
        priority_score=priority_score,
        policy_version=EXECUTIVE_AGGREGATION_POLICY_VERSION,
    )


def _build_metrics(ctx: _Context) -> dict[ExecutiveMetricKey, ExecutiveMetric]:
    total = ctx.total_repositories
    risk = ctx.risk
    modernization = ctx.modernization
    coverage = ctx.coverage
    dependencies = ctx.dependencies
    technologies = ctx.technologies

    risk_score = int(getattr(risk, "overall_score", 0) or 0)

    candidates = tuple(getattr(modernization, "candidates", ()) or ())
    theme_counts = dict(getattr(modernization, "theme_counts", ()) or ())
    theme_counts = {theme.value: count for theme, count in theme_counts.items()}
    wave_counts = dict(getattr(modernization, "wave_counts", ()) or ())
    wave_counts = {wave.value: count for wave, count in wave_counts.items()}
    candidate_count = len(candidates)
    avg_evidence_coverage = (
        mean(item.evidence_coverage for item in candidates) if candidates else 1.0
    )
    deferred_ratio = _ratio(wave_counts.get("deferred", 0), candidate_count)

    tech_count = len(technologies)
    standardized_count = sum(
        1 for item in technologies if item.standardization_status in _STANDARDIZED_STATUSES
    )
    standardized_ratio = _ratio(standardized_count, tech_count) if tech_count else 1.0

    cloud_technologies = tuple(item for item in technologies if "cloud" in item.categories)
    ai_technologies = tuple(item for item in technologies if "ai_readiness" in item.categories)
    security_technologies = tuple(item for item in technologies if "security" in item.categories)
    debt_technologies = tuple(item for item in technologies if "technical_debt" in item.categories)

    cloud_repos = {ref.value for item in cloud_technologies for ref in item.repository_references}
    ai_repos = {ref.value for item in ai_technologies for ref in item.repository_references}
    cloud_ratio = _ratio(len(cloud_repos), total)
    ai_ratio = _ratio(len(ai_repos), total)

    security_high_critical = sum(item.high_critical_finding_count for item in security_technologies)
    hotspots = tuple(getattr(risk, "hotspots", ()) or ())
    systemic_risks = tuple(getattr(risk, "systemic_risks", ()) or ())
    security_hotspots = tuple(
        item for item in hotspots if getattr(item.category, "value", None) == "security"
    )
    security_systemic = tuple(item for item in systemic_risks if "security" in item.title.lower())

    debt_candidates = tuple(
        item for item in candidates if item.theme is ModernizationTheme.REDUCE_TECHNICAL_DEBT
    )
    debt_candidate_ratio = _ratio(len(debt_candidates), total)
    debt_tech_high_critical = sum(item.high_critical_finding_count for item in debt_technologies)

    architecture_candidates = tuple(
        item for item in candidates if item.theme is ModernizationTheme.IMPROVE_ARCHITECTURE
    )
    architecture_ratio = _ratio(len(architecture_candidates), total)

    documentation_candidates = tuple(
        item for item in candidates if item.theme is ModernizationTheme.IMPROVE_DOCUMENTATION
    )
    documentation_ratio = _ratio(len(documentation_candidates), total)

    participation_pct = float(getattr(coverage, "repository_participation_percentage", 0.0) or 0.0)
    participation_ratio = participation_pct / 100.0
    freshness = getattr(coverage, "freshness", None)
    current_ratio = _ratio(getattr(freshness, "current_count", 0) or 0, total)
    graphs = getattr(coverage, "graphs", None)
    graphs_ratio = float(getattr(graphs, "coverage_ratio", 0.0) or 0.0)
    evidence = getattr(coverage, "evidence", None)
    evidence_ratio = float(getattr(evidence, "coverage_ratio", 0.0) or 0.0)

    shared_exposure_count = int(getattr(dependencies, "shared_exposure_count", 0) or 0)
    shared_exposure_ratio = _ratio(shared_exposure_count, total)

    metrics: dict[ExecutiveMetricKey, ExecutiveMetric] = {}

    health_component = 100 - risk_score
    metrics[ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH] = _metric(
        ctx,
        ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH,
        score=round(0.55 * health_component + 0.45 * participation_pct),
        confidence=0.85 if ctx.has_repositories else 0.15,
        coverage=participation_ratio,
        inputs=(
            "risk_summary.overall_score",
            "coverage_summary.repository_participation_percentage",
        ),
        calculation_rule=(
            "0.55 x (100 - portfolio_risk_score) + 0.45 x repository_participation_percentage"
        ),
    )

    metrics[ExecutiveMetricKey.PORTFOLIO_RISK] = _metric(
        ctx,
        ExecutiveMetricKey.PORTFOLIO_RISK,
        score=risk_score,
        confidence=0.85 if risk is not None and ctx.has_repositories else 0.2,
        coverage=1.0 if risk is not None else 0.0,
        inputs=("risk_summary.overall_score", "risk_summary.overall_band"),
        calculation_rule=(
            "Directly reflects PortfolioRiskSummary.overall_score; "
            "higher score indicates higher aggregate portfolio risk exposure."
        ),
    )

    if candidate_count:
        readiness_score = round(
            0.6 * (avg_evidence_coverage * 100) + 0.4 * (100 - deferred_ratio * 100)
        )
        readiness_confidence = 0.8
    else:
        readiness_score = 100 if ctx.has_repositories else 0
        readiness_confidence = 0.5 if ctx.has_repositories else 0.15
    metrics[ExecutiveMetricKey.MODERNIZATION_READINESS] = _metric(
        ctx,
        ExecutiveMetricKey.MODERNIZATION_READINESS,
        score=readiness_score,
        confidence=readiness_confidence,
        coverage=_ratio(candidate_count, max(1, total)),
        inputs=(
            "modernization_summary.candidates[].evidence_coverage",
            "modernization_summary.wave_counts",
        ),
        calculation_rule=(
            "0.6 x average(candidate.evidence_coverage) + 0.4 x (100 - deferred_wave_ratio); "
            "100 when no modernization candidates exist."
        ),
    )

    metrics[ExecutiveMetricKey.TECHNOLOGY_STANDARDIZATION] = _metric(
        ctx,
        ExecutiveMetricKey.TECHNOLOGY_STANDARDIZATION,
        score=round(standardized_ratio * 100) if tech_count else 0,
        confidence=0.8 if tech_count >= 2 else (0.4 if tech_count == 1 else 0.15),
        coverage=_ratio(tech_count, max(1, tech_count)) if tech_count else 0.0,
        inputs=("technology_inventory[].standardization_status",),
        calculation_rule=(
            "Share of technologies with standardization_status in {standard, preferred}."
        ),
    )

    metrics[ExecutiveMetricKey.ARCHITECTURE_MATURITY] = _metric(
        ctx,
        ExecutiveMetricKey.ARCHITECTURE_MATURITY,
        score=round(max(0.0, 100 - architecture_ratio * 100)),
        confidence=0.6 if candidate_count else (0.5 if ctx.has_repositories else 0.15),
        coverage=_ratio(candidate_count, max(1, total)),
        inputs=("modernization_summary.theme_counts[improve_architecture]",),
        calculation_rule="100 - (improve_architecture candidates / total repositories) x 100.",
    )

    metrics[ExecutiveMetricKey.TECHNICAL_DEBT_INDEX] = _metric(
        ctx,
        ExecutiveMetricKey.TECHNICAL_DEBT_INDEX,
        score=round(min(100.0, debt_candidate_ratio * 70 + debt_tech_high_critical * 6)),
        confidence=0.7 if (debt_candidates or debt_technologies) else (
            0.4 if ctx.has_repositories else 0.15
        ),
        coverage=_ratio(len(debt_candidates), max(1, total)),
        inputs=(
            "modernization_summary.theme_counts[reduce_technical_debt]",
            "technology_inventory[technical_debt].high_critical_finding_count",
        ),
        calculation_rule=(
            "min(100, reduce_technical_debt_candidate_ratio x 70 "
            "+ technical_debt_technology_high_critical_count x 6); higher indicates more debt."
        ),
    )

    security_penalty = min(
        100.0,
        security_high_critical * 8 + len(security_hotspots) * 12 + len(security_systemic) * 10,
    )
    metrics[ExecutiveMetricKey.SECURITY_POSTURE] = _metric(
        ctx,
        ExecutiveMetricKey.SECURITY_POSTURE,
        score=round(max(0.0, 100 - security_penalty)),
        confidence=0.75
        if (security_technologies or hotspots or systemic_risks)
        else (0.4 if ctx.has_repositories else 0.15),
        coverage=_ratio(len(security_technologies), max(1, tech_count)) if tech_count else 0.0,
        inputs=(
            "technology_inventory[security].high_critical_finding_count",
            "risk_summary.hotspots",
            "risk_summary.systemic_risks",
        ),
        calculation_rule=(
            "100 - min(100, security_tech_high_critical x 8 + security_hotspots x 12 "
            "+ security_systemic_risks x 10)."
        ),
    )

    metrics[ExecutiveMetricKey.CLOUD_ADOPTION] = _metric(
        ctx,
        ExecutiveMetricKey.CLOUD_ADOPTION,
        score=round(cloud_ratio * 100),
        confidence=0.7 if cloud_technologies else (0.4 if ctx.has_repositories else 0.15),
        coverage=cloud_ratio,
        inputs=("technology_inventory[cloud].repository_references",),
        calculation_rule="Repositories using a cloud-categorized technology / total repositories.",
    )

    metrics[ExecutiveMetricKey.AI_READINESS] = _metric(
        ctx,
        ExecutiveMetricKey.AI_READINESS,
        score=round(ai_ratio * 100),
        confidence=0.55 if ai_technologies else (0.3 if ctx.has_repositories else 0.15),
        coverage=ai_ratio,
        inputs=("technology_inventory[ai_readiness].repository_references",),
        calculation_rule=(
            "Repositories using an ai_readiness-categorized technology / total repositories."
        ),
        limitations=(_AI_HEURISTIC_LIMITATION,),
    )

    metrics[ExecutiveMetricKey.DOCUMENTATION_COVERAGE] = _metric(
        ctx,
        ExecutiveMetricKey.DOCUMENTATION_COVERAGE,
        score=round(max(0.0, 100 - documentation_ratio * 100)),
        confidence=0.6 if candidate_count else (0.45 if ctx.has_repositories else 0.15),
        coverage=_ratio(len(documentation_candidates), max(1, total)),
        inputs=("modernization_summary.theme_counts[improve_documentation]",),
        calculation_rule="100 - (improve_documentation candidates / total repositories) x 100.",
    )

    metrics[ExecutiveMetricKey.ASSESSMENT_COVERAGE] = _metric(
        ctx,
        ExecutiveMetricKey.ASSESSMENT_COVERAGE,
        score=round(participation_ratio * 100),
        confidence=0.9 if ctx.has_repositories else 0.15,
        coverage=participation_ratio,
        inputs=("coverage_summary.repository_participation_percentage",),
        calculation_rule=(
            "Directly reflects PortfolioCoverageSummary.repository_participation_percentage."
        ),
    )

    metrics[ExecutiveMetricKey.REPOSITORY_COVERAGE] = _metric(
        ctx,
        ExecutiveMetricKey.REPOSITORY_COVERAGE,
        score=round(0.5 * graphs_ratio * 100 + 0.5 * current_ratio * 100),
        confidence=0.8 if ctx.has_repositories else 0.15,
        coverage=0.5 * graphs_ratio + 0.5 * current_ratio,
        inputs=(
            "coverage_summary.graphs.coverage_ratio",
            "coverage_summary.freshness.current_count",
        ),
        calculation_rule=(
            "0.5 x graph_coverage_ratio + 0.5 x current_assessment_ratio, scaled to 0-100."
        ),
    )

    confidence_score = 0.4 * evidence_ratio + 0.3 * participation_ratio + 0.3 * graphs_ratio
    metrics[ExecutiveMetricKey.CONFIDENCE] = _metric(
        ctx,
        ExecutiveMetricKey.CONFIDENCE,
        score=round(confidence_score * 100),
        confidence=max(0.15, confidence_score) if ctx.has_repositories else 0.15,
        coverage=confidence_score,
        inputs=(
            "coverage_summary.evidence.coverage_ratio",
            "coverage_summary.repository_participation_percentage",
            "coverage_summary.graphs.coverage_ratio",
        ),
        calculation_rule=(
            "0.4 x evidence_coverage_ratio + 0.3 x repository_participation_ratio "
            "+ 0.3 x graph_coverage_ratio; represents overall confidence in this projection."
        ),
    )

    dependency_penalty = min(100.0, shared_exposure_ratio * 80)
    metrics[ExecutiveMetricKey.DEPENDENCY_HEALTH] = _metric(
        ctx,
        ExecutiveMetricKey.DEPENDENCY_HEALTH,
        score=round(max(0.0, 100 - dependency_penalty)),
        confidence=0.7 if dependencies is not None else (0.4 if ctx.has_repositories else 0.15),
        coverage=1.0 if dependencies is not None else 0.0,
        inputs=(
            "dependency_signals.shared_exposure_count",
            "dependency_signals.explicit_dependency_count",
        ),
        calculation_rule="100 - min(100, shared_exposure_count / total_repositories x 80).",
    )

    return metrics


def _build_findings(ctx: _Context) -> tuple[ExecutiveFinding, ...]:
    findings: list[ExecutiveFinding] = []
    risk = ctx.risk
    modernization = ctx.modernization
    dependencies = ctx.dependencies
    technologies = ctx.technologies

    repository_profiles = tuple(getattr(risk, "repository_profiles", ()) or ())
    for profile in sorted(repository_profiles, key=lambda item: item.score, reverse=True)[:3]:
        if profile.score <= 0:
            continue
        findings.append(
            _finding(
                ctx,
                key=f"highest-risk:{profile.repository_id.value}",
                category=ExecutiveFindingCategory.HIGHEST_RISK_REPOSITORY,
                title=f"Elevated risk concentration in repository {profile.repository_id.value}",
                summary=(
                    f"Repository {profile.repository_id.value} carries a portfolio risk score of "
                    f"{profile.score} with {profile.high_critical_count} high/critical findings."
                ),
                severity_band=_impact_band(profile.score),
                confidence=0.8,
                affected_repository_ids=(profile.repository_id.value,),
                evidence=(
                    f"score:{profile.score}",
                    f"high_critical_findings:{profile.high_critical_count}",
                    *profile.factors,
                ),
            )
        )

    candidates = tuple(getattr(modernization, "candidates", ()) or ())
    top_candidates = sorted(candidates, key=lambda item: item.priority.score, reverse=True)[:5]
    for candidate in top_candidates:
        if candidate.priority.score <= 0:
            continue
        findings.append(
            _finding(
                ctx,
                key=f"modernization:{candidate.candidate_id}",
                category=ExecutiveFindingCategory.MODERNIZATION_CANDIDATE,
                title=(
                    f"Modernization candidate: {candidate.theme.value} "
                    f"for {candidate.repository_id.value}"
                ),
                summary=(
                    f"Repository {candidate.repository_id.value} is a {candidate.wave.value} "
                    f"modernization candidate for {candidate.theme.value} "
                    f"(priority {candidate.priority.score})."
                ),
                severity_band=_band_from_value(candidate.priority.band.value),
                confidence=candidate.priority.confidence,
                affected_repository_ids=(candidate.repository_id.value,),
                evidence=(
                    f"wave:{candidate.wave.value}",
                    f"priority_score:{candidate.priority.score}",
                    *candidate.priority.contributing_factors,
                ),
            )
        )

    fragmented = tuple(
        item
        for item in technologies
        if item.standardization_status is TechnologyStandardizationStatus.FRAGMENTED
    )
    for tech in sorted(fragmented, key=lambda item: item.canonical_key)[:5]:
        findings.append(
            _finding(
                ctx,
                key=f"fragmentation:{tech.canonical_key}",
                category=ExecutiveFindingCategory.TECHNOLOGY_FRAGMENTATION,
                title=f"Fragmented technology adoption: {tech.canonical_key}",
                summary=(
                    f"Technology '{tech.canonical_key}' is fragmented across "
                    f"{tech.repository_count} repositories without a dominant standard."
                ),
                severity_band=_impact_band(min(100, tech.repository_count * 20)),
                confidence=0.75,
                affected_repository_ids=tuple(
                    ref.value for ref in tech.repository_references
                ),
                evidence=(
                    f"repository_count:{tech.repository_count}",
                    f"usage_percentage:{tech.usage_percentage}",
                ),
            )
        )

    category_groups: dict[tuple[str, ...], list[PortfolioTechnology]] = {}
    for tech in technologies:
        if not tech.categories:
            continue
        category_groups.setdefault(tech.categories, []).append(tech)
    for categories, group in sorted(category_groups.items()):
        if len(group) < 2:
            continue
        keys = tuple(sorted(item.canonical_key for item in group))
        repos = tuple(
            sorted({ref.value for item in group for ref in item.repository_references})
        )
        findings.append(
            _finding(
                ctx,
                key=f"duplication:{'-'.join(keys)}",
                category=ExecutiveFindingCategory.DUPLICATED_TECHNOLOGY_STACK,
                title=f"Duplicated technology stack in category {'/'.join(categories)}",
                summary=(
                    f"Technologies {', '.join(keys)} independently serve the same category "
                    f"({'/'.join(categories)}), indicating duplicated stacks."
                ),
                severity_band=_impact_band(min(100, len(group) * 20)),
                confidence=0.65,
                affected_repository_ids=repos,
                evidence=(f"technologies:{','.join(keys)}", f"categories:{','.join(categories)}"),
            )
        )

    obsolete = tuple(
        item
        for item in technologies
        if item.lifecycle_signal is TechnologyLifecycleSignal.OBSOLETE
    )
    for tech in sorted(obsolete, key=lambda item: item.canonical_key)[:5]:
        findings.append(
            _finding(
                ctx,
                key=f"unsupported:{tech.canonical_key}",
                category=ExecutiveFindingCategory.UNSUPPORTED_TECHNOLOGY,
                title=f"Unsupported or obsolete technology: {tech.canonical_key}",
                summary=(
                    f"Technology '{tech.canonical_key}' is flagged obsolete and is still used "
                    f"by {tech.repository_count} repositories."
                ),
                severity_band=_impact_band(min(100, 40 + tech.repository_count * 10)),
                confidence=0.7,
                affected_repository_ids=tuple(
                    ref.value for ref in tech.repository_references
                ),
                evidence=(f"lifecycle_signal:{tech.lifecycle_signal.value}",),
            )
        )

    architecture_candidates = sorted(
        (item for item in candidates if item.theme is ModernizationTheme.IMPROVE_ARCHITECTURE),
        key=lambda item: item.priority.score,
        reverse=True,
    )[:3]
    for candidate in architecture_candidates:
        findings.append(
            _finding(
                ctx,
                key=f"architecture-outlier:{candidate.candidate_id}",
                category=ExecutiveFindingCategory.ARCHITECTURE_OUTLIER,
                title=f"Architecture improvement needed: {candidate.repository_id.value}",
                summary=(
                    f"Repository {candidate.repository_id.value} shows architecture concerns "
                    f"(priority {candidate.priority.score})."
                ),
                severity_band=_band_from_value(candidate.priority.band.value),
                confidence=candidate.priority.confidence,
                affected_repository_ids=(candidate.repository_id.value,),
                evidence=(
                    f"priority_score:{candidate.priority.score}",
                    *candidate.priority.contributing_factors,
                ),
            )
        )

    hotspots = tuple(getattr(risk, "hotspots", ()) or ())
    security_hotspots = sorted(
        (item for item in hotspots if getattr(item.category, "value", None) == "security"),
        key=lambda item: item.score,
        reverse=True,
    )[:3]
    for hotspot in security_hotspots:
        findings.append(
            _finding(
                ctx,
                key=f"security-hotspot:{hotspot.hotspot_key}",
                category=ExecutiveFindingCategory.SECURITY_HOTSPOT,
                title=f"Security hotspot: {hotspot.hotspot_key}",
                summary=f"Security-related risk hotspot detected with score {hotspot.score}.",
                severity_band=_impact_band(hotspot.score),
                confidence=0.75,
                affected_repository_ids=(
                    (hotspot.repository_id.value,) if hotspot.repository_id else ()
                ),
                evidence=(f"score:{hotspot.score}", *hotspot.factors),
            )
        )
    systemic_risks = tuple(getattr(risk, "systemic_risks", ()) or ())
    security_systemic = sorted(
        (item for item in systemic_risks if "security" in item.title.lower()),
        key=lambda item: item.score,
        reverse=True,
    )[:2]
    for item in security_systemic:
        findings.append(
            _finding(
                ctx,
                key=f"security-systemic:{item.systemic_key}",
                category=ExecutiveFindingCategory.SECURITY_HOTSPOT,
                title=item.title,
                summary=(
                    f"Systemic security risk affecting {item.repository_count} repositories "
                    f"(score {item.score})."
                ),
                severity_band=_impact_band(item.score),
                confidence=0.75,
                affected_repository_ids=(),
                evidence=item.evidence,
            )
        )

    signals = tuple(getattr(dependencies, "signals", ()) or ())
    dependency_hotspots = sorted(
        (
            item
            for item in signals
            if item.is_shared_exposure and len(item.repository_ids) >= 2
        ),
        key=lambda item: len(item.repository_ids),
        reverse=True,
    )[:3]
    for signal in dependency_hotspots:
        findings.append(
            _finding(
                ctx,
                key=f"dependency-hotspot:{signal.signal_key}",
                category=ExecutiveFindingCategory.DEPENDENCY_HOTSPOT,
                title=f"Shared exposure: {signal.shared_key}",
                summary=signal.description,
                severity_band=_impact_band(min(100, len(signal.repository_ids) * 20)),
                confidence=0.7,
                affected_repository_ids=tuple(ref.value for ref in signal.repository_ids),
                evidence=(f"signal_type:{signal.signal_type.value}",),
            )
        )

    debt_candidates = sorted(
        (item for item in candidates if item.theme is ModernizationTheme.REDUCE_TECHNICAL_DEBT),
        key=lambda item: item.priority.score,
        reverse=True,
    )[:3]
    for candidate in debt_candidates:
        findings.append(
            _finding(
                ctx,
                key=f"debt-concentration:{candidate.candidate_id}",
                category=ExecutiveFindingCategory.TECHNICAL_DEBT_CONCENTRATION,
                title=f"Technical debt concentration: {candidate.repository_id.value}",
                summary=(
                    f"Repository {candidate.repository_id.value} shows concentrated technical "
                    f"debt (priority {candidate.priority.score})."
                ),
                severity_band=_band_from_value(candidate.priority.band.value),
                confidence=candidate.priority.confidence,
                affected_repository_ids=(candidate.repository_id.value,),
                evidence=(
                    f"priority_score:{candidate.priority.score}",
                    *candidate.priority.contributing_factors,
                ),
            )
        )

    risk_score = int(getattr(risk, "overall_score", 0) or 0)
    coverage = ctx.coverage
    freshness = getattr(coverage, "freshness", None)
    total = ctx.total_repositories
    current_ratio = _ratio(getattr(freshness, "current_count", 0) or 0, total)
    stale_ratio = _ratio(getattr(freshness, "stale_count", 0) or 0, total)
    tech_count = len(technologies)
    standardized_ratio = (
        _ratio(
            sum(
                1
                for item in technologies
                if item.standardization_status in _STANDARDIZED_STATUSES
            ),
            tech_count,
        )
        if tech_count
        else 0.0
    )

    if ctx.has_repositories and current_ratio >= 0.7:
        findings.append(
            _finding(
                ctx,
                key="strength:freshness",
                category=ExecutiveFindingCategory.PORTFOLIO_STRENGTH,
                title="Strong assessment freshness coverage",
                summary=(
                    f"{round(current_ratio * 100)}% of portfolio repositories have current "
                    "engineering assessments."
                ),
                severity_band=ExecutiveImpactBand.LOW,
                confidence=0.75,
                affected_repository_ids=(),
                evidence=(f"current_ratio:{round(current_ratio, 4)}",),
            )
        )
    if ctx.has_repositories and risk_score <= 20:
        findings.append(
            _finding(
                ctx,
                key="strength:low-risk",
                category=ExecutiveFindingCategory.PORTFOLIO_STRENGTH,
                title="Low aggregate portfolio risk",
                summary=f"Overall portfolio risk score is low ({risk_score}/100).",
                severity_band=ExecutiveImpactBand.LOW,
                confidence=0.75,
                affected_repository_ids=(),
                evidence=(f"overall_risk_score:{risk_score}",),
            )
        )
    if tech_count and standardized_ratio >= 0.7:
        findings.append(
            _finding(
                ctx,
                key="strength:standardization",
                category=ExecutiveFindingCategory.PORTFOLIO_STRENGTH,
                title="Strong technology standardization",
                summary=(
                    f"{round(standardized_ratio * 100)}% of tracked technologies are standard "
                    "or preferred choices."
                ),
                severity_band=ExecutiveImpactBand.LOW,
                confidence=0.7,
                affected_repository_ids=(),
                evidence=(f"standardized_ratio:{round(standardized_ratio, 4)}",),
            )
        )

    unavailable_count = int(getattr(coverage, "repositories_unavailable", 0) or 0)
    if unavailable_count > 0:
        findings.append(
            _finding(
                ctx,
                key="weakness:unavailable-repositories",
                category=ExecutiveFindingCategory.PORTFOLIO_WEAKNESS,
                title="Repositories missing published intelligence",
                summary=(
                    f"{unavailable_count} portfolio repositories have no published engineering "
                    "intelligence available."
                ),
                severity_band=_impact_band(min(100, unavailable_count * 15)),
                confidence=0.8,
                affected_repository_ids=(),
                evidence=(f"unavailable_repository_count:{unavailable_count}",),
            )
        )
    if ctx.has_repositories and stale_ratio >= 0.3:
        findings.append(
            _finding(
                ctx,
                key="weakness:stale-assessments",
                category=ExecutiveFindingCategory.PORTFOLIO_WEAKNESS,
                title="Significant stale assessment coverage",
                summary=(
                    f"{round(stale_ratio * 100)}% of portfolio repositories have stale "
                    "engineering assessments."
                ),
                severity_band=_impact_band(round(stale_ratio * 100)),
                confidence=0.75,
                affected_repository_ids=(),
                evidence=(f"stale_ratio:{round(stale_ratio, 4)}",),
            )
        )
    if len(fragmented) >= 2:
        findings.append(
            _finding(
                ctx,
                key="weakness:technology-fragmentation-breadth",
                category=ExecutiveFindingCategory.PORTFOLIO_WEAKNESS,
                title="Broad technology fragmentation across the portfolio",
                summary=(
                    f"{len(fragmented)} technologies are fragmented across the portfolio without "
                    "a dominant standard."
                ),
                severity_band=_impact_band(min(100, len(fragmented) * 15)),
                confidence=0.7,
                affected_repository_ids=(),
                evidence=(f"fragmented_technology_count:{len(fragmented)}",),
            )
        )

    return tuple(
        sorted(findings, key=lambda item: (item.category.value, item.finding_id.value))
    )


def _build_recommendations(
    ctx: _Context,
    findings: tuple[ExecutiveFinding, ...],
    metrics: dict[ExecutiveMetricKey, ExecutiveMetric],
) -> tuple[ExecutiveRecommendation, ...]:
    recommendations: list[ExecutiveRecommendation] = []
    candidates = tuple(getattr(ctx.modernization, "candidates", ()) or ())
    by_category: dict[ExecutiveFindingCategory, list[ExecutiveFinding]] = {}
    for item in findings:
        by_category.setdefault(item.category, []).append(item)

    modernization_findings = by_category.get(ExecutiveFindingCategory.MODERNIZATION_CANDIDATE, [])
    if modernization_findings:
        top = sorted(candidates, key=lambda item: item.priority.score, reverse=True)[:3]
        affected = tuple(sorted({item.repository_id.value for item in top}))
        avg_confidence = mean(item.priority.confidence for item in top) if top else 0.5
        avg_priority = round(mean(item.priority.score for item in top)) if top else 0
        recommendations.append(
            _recommendation(
                ctx,
                key=str(ExecutiveRecommendationTheme.MODERNIZATION.value),
                theme=ExecutiveRecommendationTheme.MODERNIZATION,
                title="Prioritize top modernization candidates",
                rationale=(
                    "Highest-priority modernization candidates were identified across "
                    f"{len(affected)} repositories; sequencing these first maximizes risk "
                    "reduction per unit of engineering investment."
                ),
                affected_repository_ids=affected,
                confidence=avg_confidence,
                expected_impact=_impact_band(avg_priority),
                priority_score=avg_priority,
            )
        )

    fragmentation_findings = by_category.get(
        ExecutiveFindingCategory.TECHNOLOGY_FRAGMENTATION, []
    ) + by_category.get(ExecutiveFindingCategory.DUPLICATED_TECHNOLOGY_STACK, [])
    if fragmentation_findings:
        affected = tuple(
            sorted(
                {
                    repo
                    for item in fragmentation_findings
                    for repo in item.affected_repository_ids
                }
            )
        )
        priority = min(100, len(fragmentation_findings) * 20)
        recommendations.append(
            _recommendation(
                ctx,
                key=str(ExecutiveRecommendationTheme.STANDARDIZATION.value),
                theme=ExecutiveRecommendationTheme.STANDARDIZATION,
                title="Consolidate fragmented technology choices",
                rationale=(
                    f"{len(fragmentation_findings)} technology fragmentation/duplication findings "
                    "indicate opportunity to standardize on fewer supported technologies, reducing "
                    "operational overhead."
                ),
                affected_repository_ids=affected,
                confidence=0.7,
                expected_impact=_impact_band(priority),
                priority_score=priority,
            )
        )

    debt_metric = metrics[ExecutiveMetricKey.TECHNICAL_DEBT_INDEX]
    debt_findings = by_category.get(ExecutiveFindingCategory.TECHNICAL_DEBT_CONCENTRATION, [])
    if debt_findings or debt_metric.score >= 50:
        affected = tuple(
            sorted({repo for item in debt_findings for repo in item.affected_repository_ids})
        )
        recommendations.append(
            _recommendation(
                ctx,
                key=str(ExecutiveRecommendationTheme.ENGINEERING_INVESTMENT.value),
                theme=ExecutiveRecommendationTheme.ENGINEERING_INVESTMENT,
                title="Increase investment in technical debt reduction",
                rationale=(
                    f"Technical debt index is {debt_metric.score}/100 with "
                    f"{len(debt_findings)} concentrated debt findings; sustained engineering "
                    "investment is warranted to prevent compounding risk."
                ),
                affected_repository_ids=affected,
                confidence=debt_metric.confidence,
                expected_impact=_impact_band(debt_metric.score),
                priority_score=debt_metric.score,
            )
        )

    architecture_findings = by_category.get(ExecutiveFindingCategory.ARCHITECTURE_OUTLIER, [])
    if architecture_findings:
        affected = tuple(
            sorted(
                {repo for item in architecture_findings for repo in item.affected_repository_ids}
            )
        )
        avg_confidence = mean(item.confidence for item in architecture_findings)
        priority = metrics[ExecutiveMetricKey.ARCHITECTURE_MATURITY].score
        recommendations.append(
            _recommendation(
                ctx,
                key=str(ExecutiveRecommendationTheme.ARCHITECTURE_IMPROVEMENT.value),
                theme=ExecutiveRecommendationTheme.ARCHITECTURE_IMPROVEMENT,
                title="Fund architecture remediation for outlier repositories",
                rationale=(
                    f"{len(architecture_findings)} repositories show architecture outlier "
                    "signals; targeted remediation reduces long-term maintainability risk."
                ),
                affected_repository_ids=affected,
                confidence=avg_confidence,
                expected_impact=_impact_band(100 - priority),
                priority_score=max(0, 100 - priority),
            )
        )

    dependency_findings = by_category.get(ExecutiveFindingCategory.DEPENDENCY_HOTSPOT, [])
    if dependency_findings:
        affected = tuple(
            sorted({repo for item in dependency_findings for repo in item.affected_repository_ids})
        )
        dependency_health = metrics[ExecutiveMetricKey.DEPENDENCY_HEALTH].score
        priority = max(0, 100 - dependency_health)
        recommendations.append(
            _recommendation(
                ctx,
                key=str(ExecutiveRecommendationTheme.PLATFORM_ENGINEERING.value),
                theme=ExecutiveRecommendationTheme.PLATFORM_ENGINEERING,
                title="Invest in shared platform capabilities",
                rationale=(
                    f"{len(dependency_findings)} shared-exposure dependency hotspots suggest "
                    "consolidating common capabilities into shared platform services."
                ),
                affected_repository_ids=affected,
                confidence=0.65,
                expected_impact=_impact_band(priority),
                priority_score=priority,
            )
        )

    risk_findings = by_category.get(ExecutiveFindingCategory.HIGHEST_RISK_REPOSITORY, [])
    coverage_metric = metrics[ExecutiveMetricKey.ASSESSMENT_COVERAGE]
    if risk_findings or coverage_metric.score < 70:
        affected = tuple(
            sorted({repo for item in risk_findings for repo in item.affected_repository_ids})
        )
        priority = max(0, 100 - coverage_metric.score)
        recommendations.append(
            _recommendation(
                ctx,
                key=str(ExecutiveRecommendationTheme.GOVERNANCE.value),
                theme=ExecutiveRecommendationTheme.GOVERNANCE,
                title="Strengthen engineering governance cadence",
                rationale=(
                    "Elevated repository risk concentration and/or assessment coverage gaps "
                    f"(coverage score {coverage_metric.score}/100) indicate a need for stronger "
                    "governance cadence over assessment and remediation tracking."
                ),
                affected_repository_ids=affected,
                confidence=0.7,
                expected_impact=_impact_band(priority),
                priority_score=priority,
            )
        )

    cloud_metric = metrics[ExecutiveMetricKey.CLOUD_ADOPTION]
    cloud_technologies = tuple(item for item in ctx.technologies if "cloud" in item.categories)
    if cloud_technologies and 0 < cloud_metric.score < 80:
        priority = max(0, 100 - cloud_metric.score)
        affected = tuple(
            sorted(
                {
                    ref.value
                    for item in cloud_technologies
                    for ref in item.repository_references
                }
            )
        )
        recommendations.append(
            _recommendation(
                ctx,
                key=str(ExecutiveRecommendationTheme.CLOUD_STRATEGY.value),
                theme=ExecutiveRecommendationTheme.CLOUD_STRATEGY,
                title="Expand cloud adoption coverage",
                rationale=(
                    f"Cloud adoption metric is {cloud_metric.score}/100 despite existing cloud "
                    "technology usage; broadening adoption reduces operational inconsistency."
                ),
                affected_repository_ids=affected,
                confidence=0.6,
                expected_impact=_impact_band(priority),
                priority_score=priority,
            )
        )

    ai_metric = metrics[ExecutiveMetricKey.AI_READINESS]
    if ctx.has_repositories and ai_metric.score < 50:
        priority = max(0, 100 - ai_metric.score)
        ai_technologies = tuple(
            item for item in ctx.technologies if "ai_readiness" in item.categories
        )
        affected = tuple(
            sorted(
                {
                    ref.value
                    for item in ai_technologies
                    for ref in item.repository_references
                }
            )
        )
        if not affected:
            # Fall back to all selected repositories when AI tagging is absent.
            affected = tuple(
                sorted(
                    {
                        ref.value
                        for item in ctx.technologies
                        for ref in item.repository_references
                    }
                )
            )
        recommendations.append(
            _recommendation(
                ctx,
                key=str(ExecutiveRecommendationTheme.AI_ADOPTION.value),
                theme=ExecutiveRecommendationTheme.AI_ADOPTION,
                title="Pilot AI-assisted engineering tooling",
                rationale=(
                    f"AI readiness metric is {ai_metric.score}/100; piloting AI-assisted "
                    "engineering tooling in a subset of repositories can establish a baseline "
                    "for broader adoption."
                ),
                affected_repository_ids=affected,
                confidence=0.5,
                expected_impact=_impact_band(priority),
                priority_score=priority,
            )
        )

    return tuple(sorted(recommendations, key=lambda item: item.recommendation_id.value))


def _build_observations(
    ctx: _Context,
    metrics: dict[ExecutiveMetricKey, ExecutiveMetric],
    findings: tuple[ExecutiveFinding, ...],
) -> tuple[StrategicObservation, ...]:
    observations: list[StrategicObservation] = []

    def _observation(
        key: str,
        title: str,
        summary: str,
        related_keys: tuple[ExecutiveMetricKey, ...],
        related_finding_ids: tuple[str, ...] = (),
    ) -> StrategicObservation:
        confidence = mean(metrics[item].confidence for item in related_keys)
        return StrategicObservation(
            observation_key=key,
            title=title,
            summary=summary,
            related_metric_keys=tuple(item.value for item in related_keys),
            related_finding_ids=related_finding_ids,
            confidence=confidence,
            confidence_band=_confidence_band(confidence),
        )

    risk_metric = metrics[ExecutiveMetricKey.PORTFOLIO_RISK]
    readiness_metric = metrics[ExecutiveMetricKey.MODERNIZATION_READINESS]
    if ctx.has_repositories and risk_metric.score >= 50 and readiness_metric.score < 50:
        observations.append(
            _observation(
                "risk-outpacing-modernization-readiness",
                "Portfolio risk is outpacing modernization readiness",
                (
                    f"Portfolio risk ({risk_metric.score}/100) exceeds modernization readiness "
                    f"({readiness_metric.score}/100), suggesting remediation capacity should be "
                    "expanded before risk compounds further."
                ),
                (ExecutiveMetricKey.PORTFOLIO_RISK, ExecutiveMetricKey.MODERNIZATION_READINESS),
            )
        )

    coverage_metric = metrics[ExecutiveMetricKey.ASSESSMENT_COVERAGE]
    confidence_metric = metrics[ExecutiveMetricKey.CONFIDENCE]
    if coverage_metric.score < 60:
        observations.append(
            _observation(
                "confidence-bounded-by-assessment-coverage",
                "Overall confidence is bounded by assessment coverage gaps",
                (
                    f"Assessment coverage is {coverage_metric.score}/100, which limits the "
                    f"overall confidence of this projection (confidence score "
                    f"{confidence_metric.score}/100)."
                ),
                (ExecutiveMetricKey.ASSESSMENT_COVERAGE, ExecutiveMetricKey.CONFIDENCE),
            )
        )

    standardization_metric = metrics[ExecutiveMetricKey.TECHNOLOGY_STANDARDIZATION]
    debt_metric = metrics[ExecutiveMetricKey.TECHNICAL_DEBT_INDEX]
    if standardization_metric.score < 50 and debt_metric.score >= 50:
        observations.append(
            _observation(
                "fragmentation-correlated-with-debt",
                "Technology fragmentation correlates with rising technical debt",
                (
                    f"Technology standardization is low ({standardization_metric.score}/100) "
                    f"while the technical debt index is elevated ({debt_metric.score}/100), "
                    "suggesting fragmentation is a contributing driver of debt."
                ),
                (
                    ExecutiveMetricKey.TECHNOLOGY_STANDARDIZATION,
                    ExecutiveMetricKey.TECHNICAL_DEBT_INDEX,
                ),
            )
        )

    cloud_metric = metrics[ExecutiveMetricKey.CLOUD_ADOPTION]
    security_metric = metrics[ExecutiveMetricKey.SECURITY_POSTURE]
    if cloud_metric.score >= 60 and security_metric.score < 60:
        observations.append(
            _observation(
                "cloud-adoption-outpacing-security-posture",
                "Cloud adoption is outpacing security posture",
                (
                    f"Cloud adoption is broad ({cloud_metric.score}/100) while security posture "
                    f"lags ({security_metric.score}/100); security investment should keep pace "
                    "with cloud expansion."
                ),
                (ExecutiveMetricKey.CLOUD_ADOPTION, ExecutiveMetricKey.SECURITY_POSTURE),
            )
        )

    if not ctx.has_repositories:
        observations.append(
            _observation(
                "empty-portfolio-insufficient-data",
                "Portfolio snapshot has no repositories",
                (
                    "This portfolio snapshot contains no repositories; all metrics reflect an "
                    "empty baseline and should not be used for decision-making."
                ),
                (ExecutiveMetricKey.CONFIDENCE,),
            )
        )

    return tuple(observations)


def run_executive_aggregation(portfolio_snapshot: PortfolioSnapshot) -> ExecutiveAggregationResult:
    """Deterministically project Executive Intelligence from a completed PortfolioSnapshot."""

    ctx = _build_context(portfolio_snapshot)
    metrics_by_key = _build_metrics(ctx)
    findings = _build_findings(ctx)
    recommendations = _build_recommendations(ctx, findings, metrics_by_key)
    observations = _build_observations(ctx, metrics_by_key, findings)

    metrics = tuple(metrics_by_key[key] for key in ExecutiveMetricKey)

    limitations: list[str] = []
    if not ctx.has_repositories:
        limitations.append(_EMPTY_PORTFOLIO_LIMITATION)
    unavailable = 0
    participation = 100.0
    if ctx.coverage is not None:
        unavailable = int(getattr(ctx.coverage, "repositories_unavailable", 0) or 0)
        participation = float(
            getattr(ctx.coverage, "repository_participation_percentage", 100.0) or 0.0
        )
    if unavailable > 0:
        limitations.append(
            f"{unavailable} repositories were unavailable in Portfolio Intelligence; "
            "executive coverage and confidence are reduced accordingly."
        )
    if ctx.has_repositories and participation < 100.0:
        limitations.append(
            f"Repository participation is {participation:.1f}%; incomplete assessment "
            "coverage limits executive confidence."
        )
    if ctx.dependencies is None:
        limitations.append("Dependency signals were unavailable for this portfolio snapshot.")
    limitations.append(_AI_HEURISTIC_LIMITATION)

    return ExecutiveAggregationResult(
        metrics=metrics,
        findings=findings,
        recommendations=recommendations,
        observations=observations,
        limitations=tuple(dict.fromkeys(limitations)),
    )
