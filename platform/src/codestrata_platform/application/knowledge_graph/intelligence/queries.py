"""Application queries for graph intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.domain.knowledge_graph.analysis.context import (
    GraphQueryLimits,
    ImpactDirection,
)
from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId, KnowledgeGraphId
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class TenantGraphScope:
    organization_id: OrganizationId | None = None
    workspace_id: WorkspaceId | None = None
    repository_id: RepositoryId | None = None


@dataclass(frozen=True, slots=True)
class AnalyzeComponentImpactQuery:
    graph_id: KnowledgeGraphId
    node_id: GraphNodeId
    direction: ImpactDirection = ImpactDirection.BOTH
    limits: GraphQueryLimits = field(default_factory=GraphQueryLimits)
    include_paths: bool = False
    include_diagnostics: bool = False
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class AnalyzeTechnologyImpactQuery:
    graph_id: KnowledgeGraphId
    node_id: GraphNodeId
    direction: ImpactDirection = ImpactDirection.BOTH
    limits: GraphQueryLimits = field(default_factory=GraphQueryLimits)
    include_paths: bool = False
    include_diagnostics: bool = False
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class AnalyzeFindingImpactQuery:
    graph_id: KnowledgeGraphId
    node_id: GraphNodeId
    direction: ImpactDirection = ImpactDirection.BOTH
    limits: GraphQueryLimits = field(default_factory=GraphQueryLimits)
    include_paths: bool = False
    include_diagnostics: bool = False
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class AnalyzeRecommendationImpactQuery:
    graph_id: KnowledgeGraphId
    node_id: GraphNodeId
    direction: ImpactDirection = ImpactDirection.BOTH
    limits: GraphQueryLimits = field(default_factory=GraphQueryLimits)
    include_paths: bool = False
    include_diagnostics: bool = False
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class GetFindingTraceabilityQuery:
    graph_id: KnowledgeGraphId
    node_id: GraphNodeId
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class GetRecommendationTraceabilityQuery:
    graph_id: KnowledgeGraphId
    node_id: GraphNodeId
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class GetEvidenceTraceabilityQuery:
    graph_id: KnowledgeGraphId
    node_id: GraphNodeId
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class GetGraphCoverageQuery:
    graph_id: KnowledgeGraphId
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class GetDependencyAnalysisQuery:
    graph_id: KnowledgeGraphId
    node_id: GraphNodeId | None = None
    limits: GraphQueryLimits = field(default_factory=GraphQueryLimits)
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class GetGraphRiskSummaryQuery:
    graph_id: KnowledgeGraphId
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class GetRecommendationAnalysisQuery:
    graph_id: KnowledgeGraphId
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class ValidateGraphIntegrityQuery:
    graph_id: KnowledgeGraphId
    scope: TenantGraphScope = field(default_factory=TenantGraphScope)


@dataclass(frozen=True, slots=True)
class GetRepositoryEngineeringOverviewQuery:
    repository_id: RepositoryId
    organization_id: OrganizationId | None = None
    workspace_id: WorkspaceId | None = None
