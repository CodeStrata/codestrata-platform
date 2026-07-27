"""Deterministic portfolio aggregation stages."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.application.portfolio.policies import (
    AssessmentFreshnessPolicy,
    ModernizationWavePolicy,
    RecommendationPriorityPolicy,
    TechnologyStandardizationPolicy,
    normalize_title_id,
    priority_band,
    theme_for_category,
)
from codestrata_platform.domain.engineering.aggregate import EngineeringSnapshot
from codestrata_platform.domain.engineering.enums import EngineeringSeverity
from codestrata_platform.domain.portfolio.coverage import (
    AssessmentFreshnessSummary,
    EvidenceCoverageSummary,
    GraphCoverageSummary,
    PortfolioCoverageSummary,
    RecommendationCoverageSummary,
    RepositoryCoverageStatus,
)
from codestrata_platform.domain.portfolio.finding import (
    FindingConcentration,
    PortfolioFindingCluster,
    PortfolioFindingDistribution,
    PortfolioFindingSummary,
    RecurringFindingPattern,
)
from codestrata_platform.domain.portfolio.identifiers import PortfolioTechnologyId
from codestrata_platform.domain.portfolio.lifecycle import (
    DependencySignalType,
    ModernizationTheme,
    ModernizationWave,
    RepositoryAvailabilityStatus,
    RepositoryCriticality,
    TechnologyLifecycleSignal,
)
from codestrata_platform.domain.portfolio.membership import PortfolioMembership
from codestrata_platform.domain.portfolio.modernization import (
    ModernizationCandidate,
    ModernizationConstraint,
    ModernizationPriorityScore,
    PortfolioModernizationSummary,
)
from codestrata_platform.domain.portfolio.ports import PublishedRepositoryIntelligence
from codestrata_platform.domain.portfolio.recommendation import (
    PortfolioRecommendationPriority,
    PortfolioRecommendationSummary,
    RecommendationConcentration,
    RecommendationCoverageGap,
    RecurringRecommendationPattern,
)
from codestrata_platform.domain.portfolio.risk import (
    PortfolioRiskConcentration,
    PortfolioRiskHotspot,
    PortfolioRiskSummary,
    RepositoryRiskProfile,
    SystemicRisk,
    TechnologyRiskProfile,
)
from codestrata_platform.domain.portfolio.snapshot import PortfolioRepositorySnapshotSelection
from codestrata_platform.domain.portfolio.taxonomy import (
    CrossRepositoryDependencySignal,
    SharedDependencySummary,
)
from codestrata_platform.domain.portfolio.technology import (
    PortfolioTechnology,
    PortfolioTechnologyUsage,
    TechnologyConcentration,
)
from codestrata_platform.domain.repository.ids import RepositoryId

_HIGH_SEVERITIES = {EngineeringSeverity.HIGH, EngineeringSeverity.CRITICAL}


@dataclass(frozen=True, slots=True)
class AggregationContext:
    portfolio_snapshot_id: str
    memberships: tuple[PortfolioMembership, ...]
    selections: tuple[PortfolioRepositorySnapshotSelection, ...]
    intelligence: dict[str, PublishedRepositoryIntelligence]
    evaluated_at: datetime
    standardization: TechnologyStandardizationPolicy
    freshness: AssessmentFreshnessPolicy
    priority: RecommendationPriorityPolicy
    wave: ModernizationWavePolicy
    policy_version: str


def available_snapshots(context: AggregationContext) -> tuple[EngineeringSnapshot, ...]:
    snaps: list[EngineeringSnapshot] = []
    for selection in context.selections:
        if selection.availability_status is not RepositoryAvailabilityStatus.AVAILABLE:
            continue
        intel = context.intelligence.get(selection.repository_id.value)
        if intel is not None:
            snaps.append(intel.engineering_snapshot)
    return tuple(snaps)


def aggregate_technologies(context: AggregationContext) -> tuple[PortfolioTechnology, ...]:
    selected = max(1, sum(
        1
        for item in context.selections
        if item.availability_status is RepositoryAvailabilityStatus.AVAILABLE
    ))
    by_key: dict[str, dict] = {}
    capability_keys: dict[str, set[str]] = defaultdict(set)

    for snap in available_snapshots(context):
        for tech in snap.technologies:
            bucket = by_key.setdefault(
                tech.canonical_key,
                {
                    "canonical_key": tech.canonical_key,
                    "normalized_name": tech.display_name,
                    "framework": tech.metadata.get("framework"),
                    "categories": {tech.category.value},
                    "repos": set(),
                    "usages": [],
                    "sources": set(),
                    "component_count": 0,
                    "finding_count": 0,
                    "high_critical": 0,
                    "recommendation_count": 0,
                    "production": 0,
                },
            )
            bucket["categories"].add(tech.category.value)
            bucket["repos"].add(snap.repository_id)
            bucket["sources"].add(snap.snapshot_id.value)
            production = tech.metadata.get("production_scope", "").lower() == "true"
            if production:
                bucket["production"] += 1
            finding_count = sum(
                1 for finding in snap.findings if tech.canonical_key in finding.technology_keys
            )
            high_critical = sum(
                1
                for finding in snap.findings
                if tech.canonical_key in finding.technology_keys
                and finding.severity in _HIGH_SEVERITIES
            )
            recommendation_count = sum(
                1
                for recommendation in snap.recommendations
                if recommendation.metadata.get("technology_key") == tech.canonical_key
            )
            component_count = sum(
                1
                for component in snap.components
                if component.metadata.get("technology_key") == tech.canonical_key
            )
            bucket["component_count"] += component_count
            bucket["finding_count"] += finding_count
            bucket["high_critical"] += high_critical
            bucket["recommendation_count"] += recommendation_count
            bucket["usages"].append(
                PortfolioTechnologyUsage(
                    repository_id=snap.repository_id,
                    engineering_snapshot_id=snap.snapshot_id.value,
                    component_count=component_count,
                    finding_count=finding_count,
                    high_critical_finding_count=high_critical,
                    recommendation_count=recommendation_count,
                    production_scope=production,
                )
            )
            capability = tech.metadata.get("capability") or tech.category.value
            capability_keys[capability].add(tech.canonical_key)

    fragmented_keys: set[str] = set()
    for keys in capability_keys.values():
        if len(keys) >= 2:
            # Multiple technologies for same explicit capability without a dominant standard.
            ratios = []
            for key in keys:
                repo_count = len(by_key[key]["repos"])
                ratios.append(repo_count / selected)
            if max(ratios) < context.standardization.standard_threshold:
                fragmented_keys.update(keys)

    results: list[PortfolioTechnology] = []
    for key, bucket in sorted(by_key.items()):
        repo_count = len(bucket["repos"])
        usage_pct = round(100.0 * repo_count / selected, 2)
        usage_ratio = repo_count / selected
        status = context.standardization.classify(
            usage_ratio=usage_ratio,
            repository_count=repo_count,
            fragmented=key in fragmented_keys,
        )
        results.append(
            PortfolioTechnology(
                technology_id=PortfolioTechnologyId.from_canonical(
                    portfolio_snapshot_id=context.portfolio_snapshot_id,
                    canonical_key=key,
                ),
                canonical_key=key,
                normalized_name=bucket["normalized_name"],
                framework=bucket["framework"],
                categories=tuple(sorted(bucket["categories"])),
                repository_count=repo_count,
                repository_references=tuple(
                    sorted(bucket["repos"], key=lambda item: item.value)
                ),
                component_count=bucket["component_count"],
                finding_count=bucket["finding_count"],
                high_critical_finding_count=bucket["high_critical"],
                recommendation_count=bucket["recommendation_count"],
                usage_percentage=usage_pct,
                production_usage_count=bucket["production"],
                lifecycle_signal=TechnologyLifecycleSignal.UNKNOWN,
                standardization_status=status,
                concentration=TechnologyConcentration(
                    repository_count=repo_count,
                    usage_percentage=usage_pct,
                    production_usage_count=bucket["production"],
                ),
                source_snapshot_references=tuple(sorted(bucket["sources"])),
                usages=tuple(bucket["usages"]),
            )
        )
    return tuple(results)


def aggregate_findings(context: AggregationContext) -> PortfolioFindingSummary:
    groups: dict[str, dict] = {}
    severity_totals: dict[EngineeringSeverity, int] = defaultdict(int)
    total = 0
    high_critical = 0
    repos: set[RepositoryId] = set()

    for snap in available_snapshots(context):
        recommended_findings = {
            finding_id
            for recommendation in snap.recommendations
            for finding_id in recommendation.related_finding_ids
        }
        for finding in snap.findings:
            total += 1
            repos.add(snap.repository_id)
            severity_totals[finding.severity] += 1
            if finding.severity in _HIGH_SEVERITIES:
                high_critical += 1
            title_id = normalize_title_id(finding.title)
            tech_key = finding.technology_keys[0] if finding.technology_keys else None
            recurrence_key = "|".join(
                [
                    finding.rule_id,
                    finding.category.value,
                    title_id,
                    tech_key or "",
                ]
            )
            bucket = groups.setdefault(
                recurrence_key,
                {
                    "rule_id": finding.rule_id,
                    "category": finding.category,
                    "title_id": title_id,
                    "technology_key": tech_key,
                    "repos": set(),
                    "count": 0,
                    "severities": defaultdict(int),
                    "production": 0,
                    "with_evidence": 0,
                    "with_recommendation": 0,
                    "sources": set(),
                },
            )
            bucket["repos"].add(snap.repository_id)
            bucket["count"] += 1
            bucket["severities"][finding.severity] += 1
            if finding.metadata.get("production_scope", "").lower() == "true":
                bucket["production"] += 1
            if finding.evidence_ids:
                bucket["with_evidence"] += 1
            if (
                finding.finding_id.value in recommended_findings
                or finding.source_finding_id in recommended_findings
            ):
                bucket["with_recommendation"] += 1
            bucket["sources"].add(snap.snapshot_id.value)

    patterns: list[RecurringFindingPattern] = []
    for key, bucket in sorted(groups.items()):
        repo_count = len(bucket["repos"])
        if repo_count < 1:
            continue
        patterns.append(
            RecurringFindingPattern(
                recurrence_key=hashlib.sha256(key.encode("utf-8")).hexdigest()[:32],
                rule_id=bucket["rule_id"],
                category=bucket["category"],
                normalized_title_id=bucket["title_id"],
                technology_key=bucket["technology_key"],
                repository_count=repo_count,
                finding_count=bucket["count"],
                affected_repositories=tuple(
                    sorted(bucket["repos"], key=lambda item: item.value)
                ),
                severity_distribution=tuple(
                    PortfolioFindingDistribution(severity=sev, count=count)
                    for sev, count in sorted(
                        bucket["severities"].items(),
                        key=lambda item: item[0].value,
                    )
                ),
                production_count=bucket["production"],
                evidence_coverage=round(bucket["with_evidence"] / max(1, bucket["count"]), 4),
                recommendation_coverage=round(
                    bucket["with_recommendation"] / max(1, bucket["count"]),
                    4,
                ),
                concentration=FindingConcentration(
                    repository_count=repo_count,
                    finding_count=bucket["count"],
                    production_count=bucket["production"],
                ),
                source_references=tuple(sorted(bucket["sources"])),
            )
        )

    recurring = tuple(item for item in patterns if item.repository_count >= 2)
    clusters = (
        (
            PortfolioFindingCluster(
                cluster_key="recurring",
                patterns=recurring,
            ),
        )
        if recurring
        else ()
    )
    return PortfolioFindingSummary(
        total_findings=total,
        repository_count=len(repos),
        high_critical_count=high_critical,
        recurring_patterns=recurring,
        clusters=clusters,
        severity_distribution=tuple(
            PortfolioFindingDistribution(severity=sev, count=count)
            for sev, count in sorted(severity_totals.items(), key=lambda item: item[0].value)
        ),
    )


def aggregate_recommendations(
    context: AggregationContext,
    findings: PortfolioFindingSummary,
) -> PortfolioRecommendationSummary:
    groups: dict[str, dict] = {}
    total = 0
    repos: set[RepositoryId] = set()
    criticality_lookup = {
        item.repository_id.value: item.criticality
        for item in context.memberships
        if item.is_active
    }
    selected = max(
        1,
        sum(
            1
            for item in context.selections
            if item.availability_status is RepositoryAvailabilityStatus.AVAILABLE
        ),
    )

    for snap in available_snapshots(context):
        for recommendation in snap.recommendations:
            total += 1
            repos.add(snap.repository_id)
            linked_rule = recommendation.metadata.get("linked_finding_rule")
            target_tech = recommendation.metadata.get("technology_key")
            target_component = recommendation.metadata.get("component_id")
            horizon = recommendation.metadata.get("roadmap_horizon")
            recurrence_key = "|".join(
                [
                    recommendation.source_recommendation_id,
                    recommendation.category.value,
                    recommendation.priority,
                    linked_rule or "",
                    target_tech or "",
                ]
            )
            bucket = groups.setdefault(
                recurrence_key,
                {
                    "canonical_id": recommendation.source_recommendation_id,
                    "category": recommendation.category,
                    "priority": recommendation.priority,
                    "linked_rule": linked_rule,
                    "target_tech": target_tech,
                    "target_component": target_component,
                    "horizon": horizon,
                    "repos": set(),
                    "count": 0,
                    "sources": set(),
                    "severities": set(),
                    "production": 0,
                    "criticalities": set(),
                },
            )
            bucket["repos"].add(snap.repository_id)
            bucket["count"] += 1
            bucket["sources"].add(snap.snapshot_id.value)
            bucket["severities"].add(recommendation.severity)
            bucket["criticalities"].add(
                criticality_lookup.get(
                    snap.repository_id.value,
                    RepositoryCriticality.UNSPECIFIED,
                )
            )
            if recommendation.metadata.get("production_scope", "").lower() == "true":
                bucket["production"] += 1

    patterns: list[RecurringRecommendationPattern] = []
    for key, bucket in sorted(groups.items()):
        repo_count = len(bucket["repos"])
        highest = max(
            bucket["severities"],
            key=lambda item: (
                5
                if item is EngineeringSeverity.CRITICAL
                else 4
                if item is EngineeringSeverity.HIGH
                else 3
                if item is EngineeringSeverity.MEDIUM
                else 2
                if item is EngineeringSeverity.LOW
                else 1
            ),
            default=EngineeringSeverity.UNKNOWN,
        )
        max_crit = max(
            bucket["criticalities"],
            key=lambda item: (
                4
                if item is RepositoryCriticality.MISSION_CRITICAL
                else 3
                if item is RepositoryCriticality.HIGH
                else 2
                if item is RepositoryCriticality.MEDIUM
                else 1
                if item is RepositoryCriticality.LOW
                else 0
            ),
            default=RepositoryCriticality.UNSPECIFIED,
        )
        recurring_finding_count = sum(
            1
            for pattern in findings.recurring_patterns
            if pattern.rule_id == (bucket["linked_rule"] or "")
        )
        score, band, factors = context.priority.score(
            repository_count=repo_count,
            selected_repository_count=selected,
            highest_severity=highest,
            production_count=bucket["production"],
            recurring_finding_count=recurring_finding_count,
            coverage_gap=False,
            max_criticality=max_crit,
        )
        patterns.append(
            RecurringRecommendationPattern(
                recurrence_key=hashlib.sha256(key.encode("utf-8")).hexdigest()[:32],
                canonical_recommendation_id=bucket["canonical_id"],
                category=bucket["category"],
                priority=bucket["priority"],
                linked_finding_rule=bucket["linked_rule"],
                target_technology=bucket["target_tech"],
                target_component=bucket["target_component"],
                roadmap_horizon=bucket["horizon"],
                repository_count=repo_count,
                recommendation_count=bucket["count"],
                affected_repositories=tuple(
                    sorted(bucket["repos"], key=lambda item: item.value)
                ),
                priority_score=PortfolioRecommendationPriority(
                    score=score,
                    band=band,
                    contributing_factors=factors,
                    policy_version=context.priority.version,
                ),
                concentration=RecommendationConcentration(
                    repository_count=repo_count,
                    recommendation_count=bucket["count"],
                ),
                source_references=tuple(sorted(bucket["sources"])),
            )
        )

    # Coverage gaps: high/critical findings without recommendation linkage.
    gap_groups: dict[str, dict] = {}
    for snap in available_snapshots(context):
        linked = {
            finding_id
            for recommendation in snap.recommendations
            for finding_id in recommendation.related_finding_ids
        }
        for finding in snap.findings:
            if finding.severity not in _HIGH_SEVERITIES:
                continue
            if (
                finding.finding_id.value in linked
                or finding.source_finding_id in linked
            ):
                continue
            key = f"{finding.rule_id}|{finding.category.value}"
            bucket = gap_groups.setdefault(
                key,
                {
                    "rule_id": finding.rule_id,
                    "category": finding.category,
                    "severity": finding.severity.value,
                    "repos": set(),
                    "count": 0,
                },
            )
            bucket["repos"].add(snap.repository_id)
            bucket["count"] += 1

    gaps = tuple(
        RecommendationCoverageGap(
            gap_key=hashlib.sha256(key.encode("utf-8")).hexdigest()[:32],
            finding_rule_id=bucket["rule_id"],
            category=bucket["category"],
            severity=bucket["severity"],
            repository_count=len(bucket["repos"]),
            finding_count=bucket["count"],
            affected_repositories=tuple(
                sorted(bucket["repos"], key=lambda item: item.value)
            ),
            reason="high_or_critical_finding_without_recommendation",
        )
        for key, bucket in sorted(gap_groups.items())
    )
    return PortfolioRecommendationSummary(
        total_recommendations=total,
        repository_count=len(repos),
        recurring_patterns=tuple(item for item in patterns if item.repository_count >= 2),
        coverage_gaps=gaps,
    )


def calculate_risk(
    context: AggregationContext,
    findings: PortfolioFindingSummary,
    recommendations: PortfolioRecommendationSummary,
    technologies: tuple[PortfolioTechnology, ...],
) -> PortfolioRiskSummary:
    repo_profiles: list[RepositoryRiskProfile] = []
    for snap in available_snapshots(context):
        high = sum(1 for item in snap.findings if item.severity in _HIGH_SEVERITIES)
        evidence_gaps = sum(1 for item in snap.findings if not item.evidence_ids)
        linked = {
            finding_id
            for recommendation in snap.recommendations
            for finding_id in recommendation.related_finding_ids
        }
        rec_gaps = sum(
            1
            for item in snap.findings
            if item.severity in _HIGH_SEVERITIES
            and item.finding_id.value not in linked
            and item.source_finding_id not in linked
        )
        score = min(100, high * 20 + evidence_gaps * 5 + rec_gaps * 10)
        factors = [
            f"high_critical_findings:{high}",
            f"evidence_gaps:{evidence_gaps}",
            f"recommendation_gaps:{rec_gaps}",
        ]
        repo_profiles.append(
            RepositoryRiskProfile(
                repository_id=snap.repository_id,
                score=score,
                band=priority_band(score),
                finding_count=len(snap.findings),
                high_critical_count=high,
                evidence_gap_count=evidence_gaps,
                recommendation_gap_count=rec_gaps,
                factors=tuple(factors),
            )
        )

    tech_profiles = tuple(
        TechnologyRiskProfile(
            technology_key=tech.canonical_key,
            score=min(100, tech.high_critical_finding_count * 15 + tech.repository_count * 5),
            band=priority_band(
                min(100, tech.high_critical_finding_count * 15 + tech.repository_count * 5)
            ),
            repository_count=tech.repository_count,
            high_critical_count=tech.high_critical_finding_count,
            factors=(
                f"high_critical:{tech.high_critical_finding_count}",
                f"repositories:{tech.repository_count}",
            ),
        )
        for tech in technologies
        if tech.high_critical_finding_count > 0 or tech.repository_count >= 2
    )

    systemic: list[SystemicRisk] = []
    for pattern in findings.recurring_patterns:
        if pattern.repository_count < 2:
            continue
        high_count = sum(
            item.count
            for item in pattern.severity_distribution
            if item.severity in _HIGH_SEVERITIES
        )
        if high_count <= 0:
            continue
        score = min(100, pattern.repository_count * 20 + high_count * 10)
        systemic.append(
            SystemicRisk(
                systemic_key=f"finding:{pattern.recurrence_key}",
                title=f"Recurring {pattern.category.value} finding across repositories",
                score=score,
                band=priority_band(score),
                repository_count=pattern.repository_count,
                evidence=(
                    f"rule_id:{pattern.rule_id}",
                    f"repositories:{pattern.repository_count}",
                    f"high_critical:{high_count}",
                ),
                factors=("cross_repository_high_critical_finding",),
            )
        )

    for tech in technologies:
        if tech.repository_count >= 2 and tech.high_critical_finding_count > 0:
            score = min(
                100,
                tech.repository_count * 15 + tech.high_critical_finding_count * 10,
            )
            systemic.append(
                SystemicRisk(
                    systemic_key=f"technology:{tech.canonical_key}",
                    title=f"High-risk technology used broadly: {tech.canonical_key}",
                    score=score,
                    band=priority_band(score),
                    repository_count=tech.repository_count,
                    evidence=(
                        f"technology:{tech.canonical_key}",
                        f"repositories:{tech.repository_count}",
                        f"high_critical:{tech.high_critical_finding_count}",
                    ),
                    factors=("high_risk_technology_broad_usage",),
                )
            )

    if recommendations.coverage_gaps:
        multi = [gap for gap in recommendations.coverage_gaps if gap.repository_count >= 2]
        if multi:
            score = min(100, len(multi) * 15 + sum(gap.finding_count for gap in multi) * 5)
            systemic.append(
                SystemicRisk(
                    systemic_key="recommendation-gaps",
                    title="Widespread unresolved recommendation gaps",
                    score=score,
                    band=priority_band(score),
                    repository_count=len(
                        {
                            repo.value
                            for gap in multi
                            for repo in gap.affected_repositories
                        }
                    ),
                    evidence=tuple(gap.gap_key for gap in multi[:20]),
                    factors=("widespread_recommendation_gaps",),
                )
            )

    overall = 0
    if repo_profiles:
        overall = max(item.score for item in repo_profiles)
    if systemic:
        overall = max(overall, max(item.score for item in systemic))

    concentrations = tuple(
        PortfolioRiskConcentration(
            dimension="repository",
            key=profile.repository_id.value,
            repository_count=1,
            finding_count=profile.finding_count,
            high_critical_count=profile.high_critical_count,
            score=profile.score,
            band=profile.band,
            factors=profile.factors,
        )
        for profile in sorted(repo_profiles, key=lambda item: item.score, reverse=True)[:20]
    )
    hotspots = tuple(
        PortfolioRiskHotspot(
            hotspot_key=f"repo:{profile.repository_id.value}",
            repository_id=profile.repository_id,
            technology_key=None,
            category=None,
            score=profile.score,
            band=profile.band,
            factors=profile.factors,
            source_references=(),
        )
        for profile in sorted(repo_profiles, key=lambda item: item.score, reverse=True)[:10]
        if profile.score >= 20
    )
    return PortfolioRiskSummary(
        overall_score=overall,
        overall_band=priority_band(overall),
        severity_distribution=findings.severity_distribution,
        concentrations=concentrations,
        hotspots=hotspots,
        repository_profiles=tuple(
            sorted(repo_profiles, key=lambda item: item.repository_id.value)
        ),
        technology_profiles=tuple(
            sorted(tech_profiles, key=lambda item: item.technology_key)
        ),
        systemic_risks=tuple(sorted(systemic, key=lambda item: item.systemic_key)),
        policy_version=context.policy_version,
    )


def calculate_modernization(
    context: AggregationContext,
    findings: PortfolioFindingSummary,
    recommendations: PortfolioRecommendationSummary,
    technologies: tuple[PortfolioTechnology, ...],
    risk: PortfolioRiskSummary,
) -> PortfolioModernizationSummary:
    candidates: list[ModernizationCandidate] = []
    systemic_repos = {
        evidence.split(":", 1)[-1]
        for item in risk.systemic_risks
        for evidence in item.evidence
        if evidence.startswith("repositories:")
    }

    for snap in available_snapshots(context):
        categories = {finding.category for finding in snap.findings}
        for category in sorted(categories, key=lambda item: item.value):
            theme = theme_for_category(category)
            if theme is None:
                continue
            related_findings = [
                finding.finding_id.value
                for finding in snap.findings
                if finding.category is category
            ]
            related_recs = [
                recommendation.recommendation_id.value
                for recommendation in snap.recommendations
                if recommendation.category is category
            ]
            high = sum(
                1
                for finding in snap.findings
                if finding.category is category and finding.severity in _HIGH_SEVERITIES
            )
            evidence_cov = (
                sum(
                    1
                    for finding in snap.findings
                    if finding.category is category and finding.evidence_ids
                )
                / max(1, len(related_findings))
            )
            score = min(100, high * 25 + len(related_recs) * 5 + len(related_findings) * 2)
            band = priority_band(score)
            systemic = (
                snap.repository_id.value in systemic_repos
                or any(
                    item.repository_count >= 2 and high > 0
                    for item in findings.recurring_patterns
                    if item.category is category
                )
            )
            blocked = evidence_cov < 0.25 and high > 0
            wave, wave_factors = context.wave.assign(
                priority_score=score,
                systemic=systemic,
                blocked=blocked,
                evidence_coverage=evidence_cov,
            )
            techs = sorted(
                {
                    key
                    for finding in snap.findings
                    if finding.category is category
                    for key in finding.technology_keys
                }
            )
            candidates.append(
                ModernizationCandidate(
                    candidate_id=hashlib.sha256(
                        f"{snap.repository_id.value}|{theme.value}".encode()
                    ).hexdigest()[:32],
                    repository_id=snap.repository_id,
                    theme=theme,
                    priority=ModernizationPriorityScore(
                        score=score,
                        band=band,
                        confidence=round(min(1.0, 0.4 + evidence_cov * 0.6), 4),
                        contributing_factors=(
                            f"high_critical:{high}",
                            f"findings:{len(related_findings)}",
                            f"recommendations:{len(related_recs)}",
                        ),
                        policy_version=context.wave.version,
                    ),
                    wave=wave,
                    affected_technologies=tuple(techs),
                    affected_components=(),
                    related_findings=tuple(related_findings[:50]),
                    related_recommendations=tuple(related_recs[:50]),
                    dependency_constraints=(),
                    constraints=(
                        (
                            ModernizationConstraint(
                                constraint_key="evidence",
                                description="Insufficient evidence coverage",
                                unresolved=True,
                            ),
                        )
                        if blocked
                        else ()
                    ),
                    evidence_coverage=round(evidence_cov, 4),
                    source_snapshot_references=(snap.snapshot_id.value,),
                    wave_factors=wave_factors,
                )
            )

    for tech in technologies:
        if tech.standardization_status.value == "fragmented":
            # Create standardization candidates for each affected repository.
            for repo in tech.repository_references:
                score = min(100, 40 + tech.repository_count * 5)
                wave, wave_factors = context.wave.assign(
                    priority_score=score,
                    systemic=tech.repository_count >= 2,
                    blocked=False,
                    evidence_coverage=1.0,
                )
                candidates.append(
                    ModernizationCandidate(
                        candidate_id=hashlib.sha256(
                            f"{repo.value}|standardize|{tech.canonical_key}".encode()
                        ).hexdigest()[:32],
                        repository_id=repo,
                        theme=ModernizationTheme.STANDARDIZE_TECHNOLOGY,
                        priority=ModernizationPriorityScore(
                            score=score,
                            band=priority_band(score),
                            confidence=0.9,
                            contributing_factors=(
                                "technology_fragmentation",
                                f"technology:{tech.canonical_key}",
                            ),
                            policy_version=context.wave.version,
                        ),
                        wave=wave,
                        affected_technologies=(tech.canonical_key,),
                        affected_components=(),
                        related_findings=(),
                        related_recommendations=(),
                        dependency_constraints=(),
                        constraints=(),
                        evidence_coverage=1.0,
                        source_snapshot_references=tech.source_snapshot_references,
                        wave_factors=wave_factors,
                    )
                )

    theme_counts: dict[ModernizationTheme, int] = defaultdict(int)
    wave_counts: dict[ModernizationWave, int] = defaultdict(int)
    for candidate in candidates:
        theme_counts[candidate.theme] += 1
        wave_counts[candidate.wave] += 1

    return PortfolioModernizationSummary(
        candidates=tuple(
            sorted(
                candidates,
                key=lambda item: (item.repository_id.value, item.theme.value, item.candidate_id),
            )
        ),
        theme_counts=tuple(sorted(theme_counts.items(), key=lambda item: item[0].value)),
        wave_counts=tuple(sorted(wave_counts.items(), key=lambda item: item[0].value)),
        policy_version=context.wave.version,
    )


def calculate_coverage(
    context: AggregationContext,
    findings: PortfolioFindingSummary,
) -> PortfolioCoverageSummary:
    statuses: list[RepositoryCoverageStatus] = []
    current = aging = stale = unknown = 0
    with_snap = 0
    without_assessment = 0
    with_graph = 0
    findings_total = findings.total_findings
    findings_with_evidence = 0
    high_critical = findings.high_critical_count
    high_with_recs = 0

    for selection in context.selections:
        intel = context.intelligence.get(selection.repository_id.value)
        has_snap = selection.availability_status is RepositoryAvailabilityStatus.AVAILABLE
        if has_snap:
            with_snap += 1
        else:
            without_assessment += 1
        has_graph = bool(selection.knowledge_graph_id)
        if has_graph:
            with_graph += 1
        has_retrieval = bool(intel.has_retrieval_index) if intel else False
        freshness, age = context.freshness.classify(
            published_at=intel.published_at if intel else None,
            evaluated_at=context.evaluated_at,
        )
        if freshness.value == "current":
            current += 1
        elif freshness.value == "aging":
            aging += 1
        elif freshness.value == "stale":
            stale += 1
        else:
            unknown += 1
        statuses.append(
            RepositoryCoverageStatus(
                repository_id=selection.repository_id,
                availability_status=selection.availability_status,
                has_published_snapshot=has_snap,
                has_completed_graph=has_graph,
                has_retrieval_index=has_retrieval,
                freshness_status=freshness,
                assessment_age_days=age,
                engineering_snapshot_id=selection.engineering_snapshot_id,
                selected_at=selection.selected_at,
            )
        )

    for snap in available_snapshots(context):
        linked = {
            finding_id
            for recommendation in snap.recommendations
            for finding_id in recommendation.related_finding_ids
        }
        for finding in snap.findings:
            if finding.evidence_ids:
                findings_with_evidence += 1
            if finding.severity in _HIGH_SEVERITIES and (
                finding.finding_id.value in linked or finding.source_finding_id in linked
            ):
                high_with_recs += 1

    total = len(context.selections)
    return PortfolioCoverageSummary(
        repositories_total=total,
        repositories_with_published_snapshots=with_snap,
        repositories_without_assessments=without_assessment,
        repositories_unavailable=sum(
            1
            for item in context.selections
            if item.availability_status is RepositoryAvailabilityStatus.UNAVAILABLE
        ),
        repository_participation_percentage=round(100.0 * with_snap / max(1, total), 2),
        repository_statuses=tuple(
            sorted(statuses, key=lambda item: item.repository_id.value)
        ),
        freshness=AssessmentFreshnessSummary(
            current_count=current,
            aging_count=aging,
            stale_count=stale,
            unknown_count=unknown,
            evaluated_at=context.evaluated_at,
            policy_version=context.freshness.version,
            current_threshold_days=context.freshness.current_days,
            aging_threshold_days=context.freshness.aging_days,
        ),
        evidence=EvidenceCoverageSummary(
            findings_total=findings_total,
            findings_with_evidence=findings_with_evidence,
            coverage_ratio=round(findings_with_evidence / max(1, findings_total), 4),
        ),
        recommendations=RecommendationCoverageSummary(
            high_critical_findings=high_critical,
            high_critical_with_recommendations=high_with_recs,
            coverage_ratio=round(high_with_recs / max(1, high_critical), 4),
        ),
        graphs=GraphCoverageSummary(
            repositories_with_graphs=with_graph,
            repositories_total=total,
            coverage_ratio=round(with_graph / max(1, total), 4),
        ),
        technology_coverage_count=len(
            {
                tech.canonical_key
                for snap in available_snapshots(context)
                for tech in snap.technologies
            }
        ),
    )


def calculate_dependencies(
    context: AggregationContext,
    technologies: tuple[PortfolioTechnology, ...],
    findings: PortfolioFindingSummary,
    recommendations: PortfolioRecommendationSummary,
) -> SharedDependencySummary:
    signals: list[CrossRepositoryDependencySignal] = []

    for tech in technologies:
        if tech.repository_count < 2:
            continue
        signals.append(
            CrossRepositoryDependencySignal(
                signal_key=f"shared-tech:{tech.canonical_key}",
                signal_type=DependencySignalType.SHARED_TECHNOLOGY,
                is_explicit_dependency=False,
                is_shared_exposure=True,
                repository_ids=tech.repository_references,
                shared_key=tech.canonical_key,
                description=f"Shared technology exposure: {tech.canonical_key}",
                source_references=tech.source_snapshot_references,
            )
        )
        if tech.framework:
            signals.append(
                CrossRepositoryDependencySignal(
                    signal_key=f"shared-framework:{tech.framework}:{tech.canonical_key}",
                    signal_type=DependencySignalType.SHARED_FRAMEWORK,
                    is_explicit_dependency=False,
                    is_shared_exposure=True,
                    repository_ids=tech.repository_references,
                    shared_key=tech.framework,
                    description=f"Shared framework exposure: {tech.framework}",
                    source_references=tech.source_snapshot_references,
                )
            )

    for pattern in findings.recurring_patterns:
        if pattern.repository_count < 2:
            continue
        signals.append(
            CrossRepositoryDependencySignal(
                signal_key=f"shared-risk:{pattern.recurrence_key}",
                signal_type=DependencySignalType.SHARED_RISK,
                is_explicit_dependency=False,
                is_shared_exposure=True,
                repository_ids=pattern.affected_repositories,
                shared_key=pattern.rule_id,
                description=f"Shared risk exposure for rule {pattern.rule_id}",
                source_references=pattern.source_references,
            )
        )

    for pattern in recommendations.recurring_patterns:
        if pattern.repository_count < 2:
            continue
        signals.append(
            CrossRepositoryDependencySignal(
                signal_key=f"shared-rec:{pattern.recurrence_key}",
                signal_type=DependencySignalType.SHARED_RECOMMENDATION,
                is_explicit_dependency=False,
                is_shared_exposure=True,
                repository_ids=pattern.affected_repositories,
                shared_key=pattern.canonical_recommendation_id or pattern.recurrence_key,
                description="Shared recommendation exposure",
                source_references=pattern.source_references,
            )
        )

    for repo_id, intel in sorted(context.intelligence.items()):
        for dep in intel.explicit_repository_dependencies:
            other = RepositoryId(dep)
            signals.append(
                CrossRepositoryDependencySignal(
                    signal_key=f"explicit:{repo_id}:{dep}",
                    signal_type=DependencySignalType.EXPLICIT_REPOSITORY_DEPENDENCY,
                    is_explicit_dependency=True,
                    is_shared_exposure=False,
                    repository_ids=(RepositoryId(repo_id), other),
                    shared_key=dep,
                    description="Explicit repository dependency recorded in source intelligence",
                    source_references=(intel.engineering_snapshot.snapshot_id.value,),
                )
            )

    explicit = sum(1 for item in signals if item.is_explicit_dependency)
    shared = sum(1 for item in signals if item.is_shared_exposure)
    return SharedDependencySummary(
        signals=tuple(sorted(signals, key=lambda item: item.signal_key)),
        explicit_dependency_count=explicit,
        shared_exposure_count=shared,
    )


def run_aggregation(context: AggregationContext) -> dict[str, object]:
    """Execute deterministic aggregation stages 4–11."""

    technologies = aggregate_technologies(context)
    findings = aggregate_findings(context)
    recommendations = aggregate_recommendations(context, findings)
    risk = calculate_risk(context, findings, recommendations, technologies)
    modernization = calculate_modernization(
        context,
        findings,
        recommendations,
        technologies,
        risk,
    )
    coverage = calculate_coverage(context, findings)
    dependencies = calculate_dependencies(
        context,
        technologies,
        findings,
        recommendations,
    )
    return {
        "technologies": technologies,
        "findings": findings,
        "recommendations": recommendations,
        "risk": risk,
        "modernization": modernization,
        "coverage": coverage,
        "dependencies": dependencies,
        "generated_at": context.evaluated_at,
    }
