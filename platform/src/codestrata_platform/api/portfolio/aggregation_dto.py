"""Portfolio aggregation response DTOs (replaces loosely typed dict responses)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TechnologyConcentrationDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_count: int
    usage_percentage: float
    production_usage_count: int


class PortfolioTechnologyUsageDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_id: str
    engineering_snapshot_id: str
    component_count: int
    finding_count: int
    high_critical_finding_count: int
    recommendation_count: int
    production_scope: bool = False


class PortfolioTechnologyItemDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technology_id: str
    canonical_key: str
    normalized_name: str
    framework: str | None = None
    categories: list[str] = Field(default_factory=list)
    repository_count: int
    repository_references: list[str] = Field(default_factory=list)
    component_count: int
    finding_count: int
    high_critical_finding_count: int
    recommendation_count: int
    usage_percentage: float
    production_usage_count: int
    lifecycle_signal: str
    standardization_status: str
    concentration: TechnologyConcentrationDto
    source_snapshot_references: list[str] = Field(default_factory=list)
    usages: list[PortfolioTechnologyUsageDto] = Field(default_factory=list)


class PortfolioTechnologiesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    envelope: "PortfolioEnvelopeDto"
    items: list[PortfolioTechnologyItemDto]
    total: int = Field(ge=0)


class PortfolioEnvelopeDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portfolio_id: str
    portfolio_snapshot_id: str
    portfolio_snapshot_version: int
    generated_at: datetime
    aggregation_policy_version: str
    selected_repository_count: int
    unavailable_repository_count: int
    source_snapshot_references: list[str] = Field(default_factory=list)


class FindingConcentrationDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_count: int
    finding_count: int
    production_count: int


class PortfolioFindingDistributionDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str
    count: int


class RecurringFindingPatternDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recurrence_key: str
    rule_id: str
    category: str
    normalized_title_id: str
    technology_key: str | None = None
    repository_count: int
    finding_count: int
    affected_repositories: list[str] = Field(default_factory=list)
    severity_distribution: list[PortfolioFindingDistributionDto] = Field(default_factory=list)
    production_count: int
    evidence_coverage: float
    recommendation_coverage: float
    concentration: FindingConcentrationDto
    source_references: list[str] = Field(default_factory=list)


class PortfolioFindingClusterDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cluster_key: str
    patterns: list[RecurringFindingPatternDto] = Field(default_factory=list)


class PortfolioFindingSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_findings: int
    repository_count: int
    high_critical_count: int
    recurring_patterns: list[RecurringFindingPatternDto] = Field(default_factory=list)
    clusters: list[PortfolioFindingClusterDto] = Field(default_factory=list)
    severity_distribution: list[PortfolioFindingDistributionDto] = Field(default_factory=list)


class PortfolioFindingsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    envelope: PortfolioEnvelopeDto
    summary: PortfolioFindingSummaryDto


class RecommendationConcentrationDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_count: int
    recommendation_count: int


class PortfolioRecommendationPriorityDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int
    band: str
    contributing_factors: list[str] = Field(default_factory=list)
    policy_version: str


class RecurringRecommendationPatternDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recurrence_key: str
    canonical_recommendation_id: str | None = None
    category: str
    priority: str
    linked_finding_rule: str | None = None
    target_technology: str | None = None
    target_component: str | None = None
    roadmap_horizon: str | None = None
    repository_count: int
    recommendation_count: int
    affected_repositories: list[str] = Field(default_factory=list)
    priority_score: PortfolioRecommendationPriorityDto
    concentration: RecommendationConcentrationDto
    source_references: list[str] = Field(default_factory=list)


class RecommendationCoverageGapDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gap_key: str
    finding_rule_id: str
    category: str
    severity: str
    repository_count: int
    finding_count: int
    affected_repositories: list[str] = Field(default_factory=list)
    reason: str


class PortfolioRecommendationSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_recommendations: int
    repository_count: int
    recurring_patterns: list[RecurringRecommendationPatternDto] = Field(default_factory=list)
    coverage_gaps: list[RecommendationCoverageGapDto] = Field(default_factory=list)


class PortfolioRecommendationsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    envelope: PortfolioEnvelopeDto
    summary: PortfolioRecommendationSummaryDto


class PortfolioRiskDistributionDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str
    count: int


class PortfolioRiskConcentrationDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: str
    key: str
    repository_count: int
    finding_count: int
    high_critical_count: int
    score: int
    band: str
    factors: list[str] = Field(default_factory=list)


class PortfolioRiskHotspotDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hotspot_key: str
    repository_id: str | None = None
    technology_key: str | None = None
    category: str | None = None
    score: int
    band: str
    factors: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)


class RepositoryRiskProfileDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_id: str
    score: int
    band: str
    finding_count: int
    high_critical_count: int
    evidence_gap_count: int
    recommendation_gap_count: int
    factors: list[str] = Field(default_factory=list)


class TechnologyRiskProfileDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technology_key: str
    score: int
    band: str
    repository_count: int
    high_critical_count: int
    factors: list[str] = Field(default_factory=list)


class SystemicRiskDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    systemic_key: str
    title: str
    score: int
    band: str
    repository_count: int
    evidence: list[str] = Field(default_factory=list)
    factors: list[str] = Field(default_factory=list)


class PortfolioRiskSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: int
    overall_band: str
    severity_distribution: list[PortfolioRiskDistributionDto] = Field(default_factory=list)
    concentrations: list[PortfolioRiskConcentrationDto] = Field(default_factory=list)
    hotspots: list[PortfolioRiskHotspotDto] = Field(default_factory=list)
    repository_profiles: list[RepositoryRiskProfileDto] = Field(default_factory=list)
    technology_profiles: list[TechnologyRiskProfileDto] = Field(default_factory=list)
    systemic_risks: list[SystemicRiskDto] = Field(default_factory=list)
    policy_version: str


class PortfolioRisksResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    envelope: PortfolioEnvelopeDto
    summary: PortfolioRiskSummaryDto


class ModernizationPriorityScoreDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int
    band: str
    confidence: float
    contributing_factors: list[str] = Field(default_factory=list)
    policy_version: str


class ModernizationDependencyDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dependency_key: str
    description: str
    blocking: bool


class ModernizationConstraintDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    constraint_key: str
    description: str
    unresolved: bool


class ModernizationCandidateDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    repository_id: str
    theme: str
    priority: ModernizationPriorityScoreDto
    wave: str
    affected_technologies: list[str] = Field(default_factory=list)
    affected_components: list[str] = Field(default_factory=list)
    related_findings: list[str] = Field(default_factory=list)
    related_recommendations: list[str] = Field(default_factory=list)
    dependency_constraints: list[ModernizationDependencyDto] = Field(default_factory=list)
    constraints: list[ModernizationConstraintDto] = Field(default_factory=list)
    evidence_coverage: float
    source_snapshot_references: list[str] = Field(default_factory=list)
    wave_factors: list[str] = Field(default_factory=list)


class PortfolioModernizationSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidates: list[ModernizationCandidateDto] = Field(default_factory=list)
    # Wire-compatible pairs: [theme|wave, count]
    theme_counts: list[tuple[str, int]] = Field(default_factory=list)
    wave_counts: list[tuple[str, int]] = Field(default_factory=list)
    policy_version: str


class PortfolioModernizationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    envelope: PortfolioEnvelopeDto
    summary: PortfolioModernizationSummaryDto


class RepositoryCoverageStatusDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_id: str
    availability_status: str
    has_published_snapshot: bool
    has_completed_graph: bool
    has_retrieval_index: bool
    freshness_status: str
    assessment_age_days: int | None = None
    engineering_snapshot_id: str | None = None
    selected_at: datetime | None = None


class AssessmentFreshnessSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_count: int
    aging_count: int
    stale_count: int
    unknown_count: int
    evaluated_at: datetime
    policy_version: str
    current_threshold_days: int
    aging_threshold_days: int


class EvidenceCoverageSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings_total: int
    findings_with_evidence: int
    coverage_ratio: float


class RecommendationCoverageSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    high_critical_findings: int
    high_critical_with_recommendations: int
    coverage_ratio: float


class GraphCoverageSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repositories_with_graphs: int
    repositories_total: int
    coverage_ratio: float


class PortfolioCoverageSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repositories_total: int
    repositories_with_published_snapshots: int
    repositories_without_assessments: int
    repositories_unavailable: int
    repository_participation_percentage: float
    repository_statuses: list[RepositoryCoverageStatusDto] = Field(default_factory=list)
    freshness: AssessmentFreshnessSummaryDto
    evidence: EvidenceCoverageSummaryDto
    recommendations: RecommendationCoverageSummaryDto
    graphs: GraphCoverageSummaryDto
    technology_coverage_count: int


class PortfolioCoverageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    envelope: PortfolioEnvelopeDto
    summary: PortfolioCoverageSummaryDto


class PortfolioRepositoryProfileDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_id: str
    criticality: str
    availability_status: str
    engineering_snapshot_id: str | None = None
    engineering_snapshot_version: int | None = None
    knowledge_graph_id: str | None = None
    risk_score: int | None = None
    risk_band: str | None = None
    finding_count: int
    high_critical_count: int
    technology_count: int
    recommendation_count: int
    freshness_status: str | None = None


class PortfolioRepositoryProfilesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PortfolioRepositoryProfileDto]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)


class CrossRepositoryDependencySignalDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_key: str
    signal_type: str
    is_explicit_dependency: bool
    is_shared_exposure: bool
    repository_ids: list[str] = Field(default_factory=list)
    shared_key: str
    description: str
    source_references: list[str] = Field(default_factory=list)


class SharedDependencySummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signals: list[CrossRepositoryDependencySignalDto] = Field(default_factory=list)
    explicit_dependency_count: int
    shared_exposure_count: int


class PortfolioEngineeringOverviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    envelope: PortfolioEnvelopeDto
    technologies: list[PortfolioTechnologyItemDto] = Field(default_factory=list)
    findings: PortfolioFindingSummaryDto
    recommendations: PortfolioRecommendationSummaryDto
    risk: PortfolioRiskSummaryDto
    modernization: PortfolioModernizationSummaryDto
    coverage: PortfolioCoverageSummaryDto
    dependencies: SharedDependencySummaryDto
    repository_profiles: list[PortfolioRepositoryProfileDto] = Field(default_factory=list)


# Resolve forward reference
PortfolioTechnologiesResponse.model_rebuild()
