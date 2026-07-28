"""Deterministic adapter from Executive Intelligence to presentation models.

Consumes completed Executive Intelligence only. Does not recalculate metrics,
reanalyze Portfolio Intelligence, or invoke an LLM.
"""

from __future__ import annotations

from codestrata_platform.application.executive_intelligence.models import (
    ExecutiveIntelligenceDetails,
)
from codestrata_platform.application.executive_presentation.models import (
    EXECUTIVE_PRESENTATION_POLICY_VERSION,
    EXECUTIVE_PRESENTATION_SCHEMA_VERSION,
    ExecutivePresentationModel,
    PresentationConfidenceSummary,
    PresentationCoverageSummary,
    PresentationCtoSummary,
    PresentationExecutiveSummary,
    PresentationFinding,
    PresentationIdentity,
    PresentationKpiCard,
    PresentationObservation,
    PresentationRecommendation,
    PresentationRepositoryReference,
    PresentationScorecard,
    PresentationScoreStatus,
    PresentationStrengthWeaknessItem,
    PresentationTechnologyItem,
    PresentationTechnologyLandscape,
    PresentationTrendDirection,
    PresentationTrendPoint,
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
)

_LOW_CONFIDENCE_CAVEAT = " Treat conclusions as provisional given low confidence."
_MEDIUM_CONFIDENCE_CAVEAT = " Interpret with caution given medium confidence."

_METRIC_TITLES: dict[ExecutiveMetricKey, str] = {
    ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH: "Overall Engineering Health",
    ExecutiveMetricKey.PORTFOLIO_RISK: "Portfolio Risk",
    ExecutiveMetricKey.MODERNIZATION_READINESS: "Modernization Readiness",
    ExecutiveMetricKey.TECHNOLOGY_STANDARDIZATION: "Technology Standardization",
    ExecutiveMetricKey.ARCHITECTURE_MATURITY: "Architecture Maturity",
    ExecutiveMetricKey.TECHNICAL_DEBT_INDEX: "Technical Debt Index",
    ExecutiveMetricKey.SECURITY_POSTURE: "Security Posture",
    ExecutiveMetricKey.CLOUD_ADOPTION: "Cloud Adoption",
    ExecutiveMetricKey.AI_READINESS: "AI Readiness",
    ExecutiveMetricKey.DOCUMENTATION_COVERAGE: "Documentation Coverage",
    ExecutiveMetricKey.ASSESSMENT_COVERAGE: "Assessment Coverage",
    ExecutiveMetricKey.REPOSITORY_COVERAGE: "Repository Coverage",
    ExecutiveMetricKey.CONFIDENCE: "Confidence",
    ExecutiveMetricKey.DEPENDENCY_HEALTH: "Dependency Health",
}

_METRIC_DESCRIPTIONS: dict[ExecutiveMetricKey, str] = {
    ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH: (
        "Composite leadership view of portfolio engineering health."
    ),
    ExecutiveMetricKey.PORTFOLIO_RISK: (
        "Aggregate portfolio risk exposure derived from Portfolio Intelligence."
    ),
    ExecutiveMetricKey.MODERNIZATION_READINESS: (
        "Readiness to execute modernization work across the portfolio."
    ),
    ExecutiveMetricKey.TECHNOLOGY_STANDARDIZATION: (
        "Degree of technology standardization across repositories."
    ),
    ExecutiveMetricKey.ARCHITECTURE_MATURITY: (
        "Architecture maturity inferred from modernization and finding signals."
    ),
    ExecutiveMetricKey.TECHNICAL_DEBT_INDEX: (
        "Concentration of technical debt across the portfolio."
    ),
    ExecutiveMetricKey.SECURITY_POSTURE: (
        "Portfolio security posture based on security findings and hotspots."
    ),
    ExecutiveMetricKey.CLOUD_ADOPTION: (
        "Share of repositories with cloud-categorized technology usage."
    ),
    ExecutiveMetricKey.AI_READINESS: (
        "Share of repositories with AI-readiness technology tagging."
    ),
    ExecutiveMetricKey.DOCUMENTATION_COVERAGE: (
        "Documentation coverage inferred from modernization candidates."
    ),
    ExecutiveMetricKey.ASSESSMENT_COVERAGE: (
        "Assessment participation across portfolio repositories."
    ),
    ExecutiveMetricKey.REPOSITORY_COVERAGE: (
        "Repository-level knowledge and freshness coverage."
    ),
    ExecutiveMetricKey.CONFIDENCE: (
        "Aggregate confidence of Executive Intelligence projections."
    ),
    ExecutiveMetricKey.DEPENDENCY_HEALTH: (
        "Dependency health based on shared exposure and dependency signals."
    ),
}

# Higher score is worse for these metrics.
_INVERTED_SCORE_KEYS: frozenset[ExecutiveMetricKey] = frozenset(
    {
        ExecutiveMetricKey.PORTFOLIO_RISK,
        ExecutiveMetricKey.TECHNICAL_DEBT_INDEX,
    }
)

_TECHNOLOGY_FINDING_CATEGORIES: frozenset[ExecutiveFindingCategory] = frozenset(
    {
        ExecutiveFindingCategory.TECHNOLOGY_FRAGMENTATION,
        ExecutiveFindingCategory.DUPLICATED_TECHNOLOGY_STACK,
        ExecutiveFindingCategory.UNSUPPORTED_TECHNOLOGY,
    }
)


def score_status_for_metric(key: ExecutiveMetricKey, score: int) -> PresentationScoreStatus:
    """Map a preserved metric score to a deterministic presentation status."""

    clamped = max(0, min(100, int(score)))
    effective = (100 - clamped) if key in _INVERTED_SCORE_KEYS else clamped
    if effective >= 85:
        return PresentationScoreStatus.EXCELLENT
    if effective >= 70:
        return PresentationScoreStatus.GOOD
    if effective >= 45:
        return PresentationScoreStatus.FAIR
    if effective >= 25:
        return PresentationScoreStatus.POOR
    return PresentationScoreStatus.CRITICAL


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _metric_map(details: ExecutiveIntelligenceDetails) -> dict[ExecutiveMetricKey, ExecutiveMetric]:
    return {item.key: item for item in details.metrics}


def _require_metric(
    metrics: dict[ExecutiveMetricKey, ExecutiveMetric],
    key: ExecutiveMetricKey,
) -> ExecutiveMetric:
    metric = metrics.get(key)
    if metric is None:
        raise ValueError(f"Missing required executive metric '{key.value}'")
    return metric


def _kpi_card(metric: ExecutiveMetric) -> PresentationKpiCard:
    return PresentationKpiCard(
        identifier=metric.metric_id.value,
        metric_key=metric.key,
        title=_METRIC_TITLES[metric.key],
        score=metric.score,
        status=score_status_for_metric(metric.key, metric.score),
        confidence=metric.confidence,
        confidence_band=metric.confidence_band,
        coverage=metric.coverage,
        description=_METRIC_DESCRIPTIONS[metric.key],
        calculation_disclosure=metric.calculation_rule,
        limitations=metric.limitations,
        drill_down_reference=f"executive-metric:{metric.key.value}",
        inputs=metric.inputs,
    )


def _presentation_finding(item: ExecutiveFinding) -> PresentationFinding:
    limitations: list[str] = []
    if item.confidence_band is ExecutiveConfidenceBand.LOW:
        limitations.append(
            "Finding confidence is low; treat as directional rather than definitive."
        )
    return PresentationFinding(
        finding_id=item.finding_id.value,
        title=item.title,
        category=item.category,
        severity=item.severity_band,
        description=item.summary,
        affected_repository_ids=item.affected_repository_ids,
        confidence=item.confidence,
        confidence_band=item.confidence_band,
        evidence_references=item.evidence,
        source_references=item.source_references,
        limitations=tuple(limitations),
    )


def _confidence_caveat(band: ExecutiveConfidenceBand) -> str:
    if band is ExecutiveConfidenceBand.LOW:
        return _LOW_CONFIDENCE_CAVEAT
    if band is ExecutiveConfidenceBand.MEDIUM:
        return _MEDIUM_CONFIDENCE_CAVEAT
    return ""


def _presentation_recommendation(
    item: ExecutiveRecommendation,
) -> PresentationRecommendation:
    limitations: list[str] = []
    if item.confidence_band is ExecutiveConfidenceBand.LOW:
        limitations.append(
            "Recommendation confidence is low; validate before committing investment."
        )
    return PresentationRecommendation(
        recommendation_id=item.recommendation_id.value,
        title=item.title,
        theme=item.theme,
        priority_score=item.priority_score,
        rationale=item.rationale,
        expected_impact=item.expected_impact,
        affected_repository_ids=item.affected_repository_ids,
        confidence=item.confidence,
        confidence_band=item.confidence_band,
        # Executive Intelligence does not expose recommendation→finding links.
        supporting_finding_ids=(),
        source_references=item.source_references,
        limitations=tuple(limitations),
    )


def _modernization_outlook(metric: ExecutiveMetric) -> str:
    status = score_status_for_metric(metric.key, metric.score)
    if status is PresentationScoreStatus.EXCELLENT:
        outlook = (
            f"Modernization readiness is excellent ({metric.score}/100); "
            "the portfolio is well positioned for planned modernization waves."
        )
    elif status is PresentationScoreStatus.GOOD:
        outlook = (
            f"Modernization readiness is good ({metric.score}/100); "
            "prioritize the highest-impact candidates first."
        )
    elif status is PresentationScoreStatus.FAIR:
        outlook = (
            f"Modernization readiness is fair ({metric.score}/100); "
            "improve evidence coverage before expanding modernization scope."
        )
    elif status is PresentationScoreStatus.POOR:
        outlook = (
            f"Modernization readiness is poor ({metric.score}/100); "
            "stabilize assessment coverage and reduce deferred work before scaling."
        )
    else:
        outlook = (
            f"Modernization readiness is critical ({metric.score}/100); "
            "address foundational coverage and high-priority debt before broad programs."
        )
    return outlook + _confidence_caveat(metric.confidence_band)


def _confidence_statement(
    confidence_metric: ExecutiveMetric | None,
    average_confidence: float,
) -> str:
    if confidence_metric is not None:
        return (
            f"Executive confidence score is {confidence_metric.score}/100 "
            f"({confidence_metric.confidence_band.value} band, "
            f"metric confidence {confidence_metric.confidence:.2f})."
            + _confidence_caveat(confidence_metric.confidence_band)
        )
    return (
        f"Average metric confidence is {average_confidence:.2f}; "
        "interpret conclusions with corresponding caution."
    )


def _coverage_statement(
    assessment: ExecutiveMetric | None,
    repository: ExecutiveMetric | None,
) -> str:
    parts: list[str] = []
    if assessment is not None:
        parts.append(f"assessment coverage {assessment.score}/100")
    if repository is not None:
        parts.append(f"repository coverage {repository.score}/100")
    if not parts:
        return "Coverage metrics were unavailable for this projection."
    return "Coverage signals: " + "; ".join(parts) + "."


def _strength_weakness_items(
    details: ExecutiveIntelligenceDetails,
    *,
    strength: bool,
) -> tuple[PresentationStrengthWeaknessItem, ...]:
    category = (
        ExecutiveFindingCategory.PORTFOLIO_STRENGTH
        if strength
        else ExecutiveFindingCategory.PORTFOLIO_WEAKNESS
    )
    items: list[PresentationStrengthWeaknessItem] = []
    for finding in details.findings:
        if finding.category is not category:
            continue
        definitive = finding.confidence_band is not ExecutiveConfidenceBand.LOW
        items.append(
            PresentationStrengthWeaknessItem(
                key=finding.finding_id.value,
                title=finding.title,
                summary=finding.summary,
                related_metric_keys=(),
                related_finding_ids=(finding.finding_id.value,),
                confidence=finding.confidence,
                confidence_band=finding.confidence_band,
                definitive=definitive,
            )
        )
    return tuple(items)


def _technology_landscape(
    details: ExecutiveIntelligenceDetails,
) -> PresentationTechnologyLandscape:
    fragmentation: list[PresentationTechnologyItem] = []
    duplicated: list[PresentationTechnologyItem] = []
    unsupported: list[PresentationTechnologyItem] = []
    opportunities: list[PresentationTechnologyItem] = []

    for finding in details.findings:
        if finding.category not in _TECHNOLOGY_FINDING_CATEGORIES:
            continue
        item = PresentationTechnologyItem(
            key=finding.finding_id.value,
            title=finding.title,
            category=finding.category.value,
            summary=finding.summary,
            affected_repository_ids=finding.affected_repository_ids,
            confidence=finding.confidence,
            evidence_references=finding.evidence,
            source_references=finding.source_references,
        )
        if finding.category is ExecutiveFindingCategory.TECHNOLOGY_FRAGMENTATION:
            fragmentation.append(item)
        elif finding.category is ExecutiveFindingCategory.DUPLICATED_TECHNOLOGY_STACK:
            duplicated.append(item)
        else:
            unsupported.append(item)

    for recommendation in details.recommendations:
        if recommendation.theme is not ExecutiveRecommendationTheme.STANDARDIZATION:
            continue
        opportunities.append(
            PresentationTechnologyItem(
                key=recommendation.recommendation_id.value,
                title=recommendation.title,
                category=recommendation.theme.value,
                summary=recommendation.rationale,
                affected_repository_ids=recommendation.affected_repository_ids,
                confidence=recommendation.confidence,
                evidence_references=(),
                source_references=recommendation.source_references,
            )
        )

    limitations: list[str] = [
        "Technology landscape projects Executive Intelligence findings only; "
        "it does not re-inventory Portfolio technology catalogs."
    ]
    if not (fragmentation or duplicated or unsupported or opportunities):
        limitations.append(
            "No technology fragmentation, duplication, unsupported-tech, or "
            "standardization findings were present in this Executive Intelligence snapshot."
        )
    return PresentationTechnologyLandscape(
        fragmentation=tuple(fragmentation),
        duplicated_stacks=tuple(duplicated),
        unsupported_technologies=tuple(unsupported),
        standardization_opportunities=tuple(opportunities),
        limitations=tuple(limitations),
    )


def _repository_references(
    details: ExecutiveIntelligenceDetails,
) -> tuple[PresentationRepositoryReference, ...]:
    # Preserve first-seen order from Executive Intelligence findings then recommendations.
    ids: list[str] = []
    seen: set[str] = set()
    for finding in details.findings:
        for repo_id in finding.affected_repository_ids:
            if repo_id not in seen:
                seen.add(repo_id)
                ids.append(repo_id)
    for recommendation in details.recommendations:
        for repo_id in recommendation.affected_repository_ids:
            if repo_id not in seen:
                seen.add(repo_id)
                ids.append(repo_id)
    # Display metadata is not present on Executive Intelligence; leave enrichment fields null.
    return tuple(
        PresentationRepositoryReference(
            repository_id=repo_id,
            display_name=None,
            snapshot_id=None,
            status=None,
            participation_state=None,
        )
        for repo_id in ids
    )


def _executive_summary(
    details: ExecutiveIntelligenceDetails,
    metrics: dict[ExecutiveMetricKey, ExecutiveMetric],
    kpi_by_key: dict[ExecutiveMetricKey, PresentationKpiCard],
    recommendations: tuple[PresentationRecommendation, ...],
    strengths: tuple[PresentationStrengthWeaknessItem, ...],
    weaknesses: tuple[PresentationStrengthWeaknessItem, ...],
) -> PresentationExecutiveSummary:
    health = _require_metric(metrics, ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH)
    risk = _require_metric(metrics, ExecutiveMetricKey.PORTFOLIO_RISK)
    modernization = _require_metric(metrics, ExecutiveMetricKey.MODERNIZATION_READINESS)
    health_status = kpi_by_key[health.key].status
    risk_status = kpi_by_key[risk.key].status

    headline = (
        f"Portfolio engineering health is {health_status.value} ({health.score}/100) "
        f"with {risk_status.value} portfolio risk ({risk.score}/100)."
        + _confidence_caveat(health.confidence_band)
    )

    # Only definitive (non-low-confidence) strengths/weaknesses are presented as major.
    major_strengths = tuple(item.title for item in strengths if item.definitive)[:5]
    major_weaknesses = tuple(item.title for item in weaknesses if item.definitive)[:5]
    top_recs = tuple(
        item.title
        for item in sorted(
            recommendations,
            key=lambda rec: (-rec.priority_score, rec.recommendation_id),
        )[:5]
    )

    return PresentationExecutiveSummary(
        headline=headline,
        overall_engineering_health=health.score,
        overall_health_status=health_status,
        portfolio_risk=risk.score,
        portfolio_risk_status=risk_status,
        modernization_outlook=_modernization_outlook(modernization),
        major_strengths=major_strengths,
        major_weaknesses=major_weaknesses,
        highest_priority_recommendations=top_recs,
        confidence_statement=_confidence_statement(
            metrics.get(ExecutiveMetricKey.CONFIDENCE),
            _avg([item.confidence for item in details.metrics]),
        ),
        coverage_statement=_coverage_statement(
            metrics.get(ExecutiveMetricKey.ASSESSMENT_COVERAGE),
            metrics.get(ExecutiveMetricKey.REPOSITORY_COVERAGE),
        ),
        limitations=details.limitations,
    )


def _cto_summary(
    kpi_by_key: dict[ExecutiveMetricKey, PresentationKpiCard],
    findings: tuple[PresentationFinding, ...],
    recommendations: tuple[PresentationRecommendation, ...],
    limitations: tuple[str, ...],
) -> PresentationCtoSummary:
    critical_findings = tuple(
        item
        for item in findings
        if item.severity in {ExecutiveImpactBand.CRITICAL, ExecutiveImpactBand.HIGH}
    )
    strategic_priorities = tuple(
        sorted(
            recommendations,
            key=lambda rec: (-rec.priority_score, rec.recommendation_id),
        )[:8]
    )
    return PresentationCtoSummary(
        engineering_health=kpi_by_key[ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH],
        architecture_maturity=kpi_by_key[ExecutiveMetricKey.ARCHITECTURE_MATURITY],
        technical_debt=kpi_by_key[ExecutiveMetricKey.TECHNICAL_DEBT_INDEX],
        security_posture=kpi_by_key[ExecutiveMetricKey.SECURITY_POSTURE],
        dependency_health=kpi_by_key[ExecutiveMetricKey.DEPENDENCY_HEALTH],
        technology_standardization=kpi_by_key[ExecutiveMetricKey.TECHNOLOGY_STANDARDIZATION],
        modernization_readiness=kpi_by_key[ExecutiveMetricKey.MODERNIZATION_READINESS],
        cloud_adoption=kpi_by_key[ExecutiveMetricKey.CLOUD_ADOPTION],
        ai_readiness=kpi_by_key[ExecutiveMetricKey.AI_READINESS],
        critical_findings=critical_findings,
        strategic_priorities=strategic_priorities,
        limitations=limitations,
    )


def _confidence_summary(
    details: ExecutiveIntelligenceDetails,
    metrics: dict[ExecutiveMetricKey, ExecutiveMetric],
) -> PresentationConfidenceSummary:
    confidence_metric = metrics.get(ExecutiveMetricKey.CONFIDENCE)
    low_keys = tuple(
        sorted(
            item.key.value
            for item in details.metrics
            if item.confidence_band is ExecutiveConfidenceBand.LOW
        )
    )
    # Preserve exact Executive Intelligence limitations; do not invent or slice.
    return PresentationConfidenceSummary(
        overall_confidence_score=confidence_metric.score if confidence_metric else None,
        overall_confidence=confidence_metric.confidence if confidence_metric else None,
        overall_confidence_band=(
            confidence_metric.confidence_band if confidence_metric else None
        ),
        metric_confidence_average=_avg([item.confidence for item in details.metrics]),
        finding_confidence_average=_avg([item.confidence for item in details.findings]),
        recommendation_confidence_average=_avg(
            [item.confidence for item in details.recommendations]
        ),
        low_confidence_metric_keys=low_keys,
        limitations=details.limitations,
    )


def _coverage_summary(
    details: ExecutiveIntelligenceDetails,
    metrics: dict[ExecutiveMetricKey, ExecutiveMetric],
) -> PresentationCoverageSummary:
    assessment = metrics.get(ExecutiveMetricKey.ASSESSMENT_COVERAGE)
    repository = metrics.get(ExecutiveMetricKey.REPOSITORY_COVERAGE)
    incomplete = tuple(
        sorted(item.key.value for item in details.metrics if item.coverage < 1.0)
    )
    # Preserve exact Executive Intelligence limitations; do not invent coverage text.
    return PresentationCoverageSummary(
        assessment_coverage_score=assessment.score if assessment else None,
        repository_coverage_score=repository.score if repository else None,
        assessment_coverage=assessment.coverage if assessment else None,
        repository_coverage=repository.coverage if repository else None,
        metric_coverage_average=_avg([item.coverage for item in details.metrics]),
        incomplete_metric_keys=incomplete,
        limitations=details.limitations,
    )


def project_executive_presentation(
    details: ExecutiveIntelligenceDetails,
) -> ExecutivePresentationModel:
    """Project a completed Executive Intelligence snapshot into presentation models."""

    if details.summary.status is not ExecutiveIntelligenceStatus.COMPLETED:
        raise ValueError(
            "Executive Presentation requires a completed Executive Intelligence snapshot"
        )

    metrics = _metric_map(details)
    # Preserve Executive Intelligence metric ordering exactly.
    kpi_cards = tuple(_kpi_card(item) for item in details.metrics)
    kpi_by_key = {card.metric_key: card for card in kpi_cards}

    findings = tuple(_presentation_finding(item) for item in details.findings)
    recommendations = tuple(
        _presentation_recommendation(item) for item in details.recommendations
    )
    observations = tuple(
        PresentationObservation(
            observation_key=item.observation_key,
            title=item.title,
            summary=item.summary,
            related_metric_keys=item.related_metric_keys,
            related_finding_ids=item.related_finding_ids,
            confidence=item.confidence,
            confidence_band=item.confidence_band,
        )
        for item in details.observations
    )

    strengths = _strength_weakness_items(details, strength=True)
    weaknesses = _strength_weakness_items(details, strength=False)
    identity = PresentationIdentity(
        executive_intelligence_id=details.summary.executive_intelligence_id,
        organization_id=details.summary.organization_id,
        workspace_id=details.summary.workspace_id,
        portfolio_id=details.summary.portfolio_id,
        portfolio_snapshot_id=details.summary.portfolio_snapshot_id,
        portfolio_snapshot_version=details.summary.portfolio_snapshot_version,
        executive_version=details.summary.version,
        projection_completed_at=details.summary.completed_at,
        schema_version=EXECUTIVE_PRESENTATION_SCHEMA_VERSION,
        policy_version=EXECUTIVE_PRESENTATION_POLICY_VERSION,
        source_policy_version=details.summary.policy_version,
        source_schema_version=details.summary.schema_version,
    )

    trend_ready = tuple(
        PresentationTrendPoint(
            metric_key=card.metric_key,
            current_value=card.score,
            snapshot_timestamp=details.summary.completed_at,
            portfolio_snapshot_id=details.summary.portfolio_snapshot_id,
            executive_intelligence_id=details.summary.executive_intelligence_id,
            comparison_metadata={
                "executive_version": str(details.summary.version),
                "portfolio_snapshot_version": str(details.summary.portfolio_snapshot_version),
            },
            direction=PresentationTrendDirection.UNKNOWN,
        )
        for card in kpi_cards
    )

    return ExecutivePresentationModel(
        identity=identity,
        executive_summary=_executive_summary(
            details,
            metrics,
            kpi_by_key,
            recommendations,
            strengths,
            weaknesses,
        ),
        cto_summary=_cto_summary(
            kpi_by_key,
            findings,
            recommendations,
            details.limitations,
        ),
        portfolio_scorecard=PresentationScorecard(
            title="Portfolio Scorecard",
            cards=kpi_cards,
        ),
        kpi_cards=kpi_cards,
        portfolio_health=kpi_by_key[ExecutiveMetricKey.OVERALL_ENGINEERING_HEALTH],
        portfolio_risk=kpi_by_key[ExecutiveMetricKey.PORTFOLIO_RISK],
        modernization_readiness=kpi_by_key[ExecutiveMetricKey.MODERNIZATION_READINESS],
        technology_landscape=_technology_landscape(details),
        architecture_posture=kpi_by_key[ExecutiveMetricKey.ARCHITECTURE_MATURITY],
        technical_debt_posture=kpi_by_key[ExecutiveMetricKey.TECHNICAL_DEBT_INDEX],
        security_posture=kpi_by_key[ExecutiveMetricKey.SECURITY_POSTURE],
        dependency_posture=kpi_by_key[ExecutiveMetricKey.DEPENDENCY_HEALTH],
        cloud_posture=kpi_by_key[ExecutiveMetricKey.CLOUD_ADOPTION],
        ai_readiness=kpi_by_key[ExecutiveMetricKey.AI_READINESS],
        engineering_strengths=strengths,
        engineering_weaknesses=weaknesses,
        findings=findings,
        recommendations=recommendations,
        observations=observations,
        confidence_summary=_confidence_summary(details, metrics),
        coverage_summary=_coverage_summary(details, metrics),
        limitations_and_assumptions=details.limitations,
        repository_references=_repository_references(details),
        trend_ready_metrics=trend_ready,
    )


class ExecutivePresentationAdapter:
    """Single boundary from Executive Intelligence to presentation models."""

    def adapt(self, details: ExecutiveIntelligenceDetails) -> ExecutivePresentationModel:
        return project_executive_presentation(details)
