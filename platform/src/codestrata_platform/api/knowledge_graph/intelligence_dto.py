"""API DTOs for graph intelligence."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImpactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: str = Field(default="both", max_length=16)
    max_depth: int = Field(default=5, ge=1, le=10)
    maximum_nodes: int = Field(default=500, ge=1, le=5000)
    maximum_edges: int = Field(default=1000, ge=1, le=10000)
    maximum_paths: int = Field(default=25, ge=1, le=100)
    include_paths: bool = False
    include_diagnostics: bool = False


class ImpactFactorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    description: str
    points: int
    source_node_ids: list[str]
    source_edge_ids: list[str]


class ImpactPathResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_ids: list[str]
    edge_ids: list[str]


class ImpactAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    subject_node_id: str
    subject_node_type: str
    score: int
    severity: str
    policy_version: str
    contributing_factors: list[ImpactFactorResponse]
    impacted_node_ids: list[str]
    source_node_ids: list[str]
    source_edge_ids: list[str]
    paths: list[ImpactPathResponse]
    diagnostics: list[str]


class TraceabilityGapResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gap_type: str
    node_id: str
    message: str


class TraceabilityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    subject_node_id: str
    subject_node_type: str
    related: dict[str, list[str]]
    edge_ids: list[str]
    gaps: list[TraceabilityGapResponse]


class CoverageMetricResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numerator: int
    denominator: int
    percentage: float | None


class CoverageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    findings_with_evidence: CoverageMetricResponse
    high_critical_with_recommendations: CoverageMetricResponse
    findings_linked_to_components: CoverageMetricResponse
    technologies_linked_to_components: CoverageMetricResponse
    recommendations_linked_to_findings: CoverageMetricResponse
    objects_with_source_reference: CoverageMetricResponse


class DependencyHotspotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    display_name: str
    fan_in: int
    fan_out: int
    kind: str


class DependencyCycleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_ids: list[str]
    edge_ids: list[str]


class DependencyAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    direct_dependencies: list[str]
    transitive_dependencies: list[str]
    upstream_dependencies: list[str]
    downstream_dependencies: list[str]
    cycles: list[DependencyCycleResponse]
    hotspots: list[DependencyHotspotResponse]
    orphan_component_ids: list[str]
    maximum_depth: int


class RiskHotspotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    node_type: str
    display_name: str
    score: int
    factors: list[str]


class RiskSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    by_severity: dict[str, int]
    by_category: dict[str, int]
    hotspots: list[RiskHotspotResponse]
    unresolved_finding_ids: list[str]


class RecommendationStepResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    display_name: str
    priority: str
    order: int


class RecommendationAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    total: int
    linked_to_findings: int
    execution_order: list[RecommendationStepResponse]
    cycles: list[list[str]]
    conflict_count: int


class IntegrityIssueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_type: str
    severity: str
    message: str
    node_ids: list[str]
    edge_ids: list[str]


class IntegrityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    integrity_version: str
    passed: bool
    issue_count: int
    critical_issue_count: int
    issues: list[IntegrityIssueResponse]


class RepositoryOverviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    repository_id: str
    technology_count: int
    component_count: int
    finding_distribution: dict[str, int]
    recommendation_count: int
    evidence_coverage: CoverageMetricResponse
    recommendation_coverage: CoverageMetricResponse
    dependency_hotspots: list[DependencyHotspotResponse]
    risk_hotspots: list[RiskHotspotResponse]
    highest_impact_components: list[str]
    highest_impact_technologies: list[str]
    integrity_passed: bool
    policy_version: str
