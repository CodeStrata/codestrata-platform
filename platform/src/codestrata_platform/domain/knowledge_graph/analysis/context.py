"""Shared query context, limits, and traceability for graph intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.analysis.errors import GraphAnalysisLimitError
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.knowledge_graph.lifecycle import GraphVersion
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId

DEFAULT_MAX_DEPTH = 5
DEFAULT_MAX_NODES = 500
DEFAULT_MAX_EDGES = 1000
DEFAULT_MAX_PATHS = 25
DEFAULT_TIMEOUT_MS = 5_000

HARD_MAX_DEPTH = 10
HARD_MAX_NODES = 5_000
HARD_MAX_EDGES = 10_000
HARD_MAX_PATHS = 100


class ImpactDirection(StrEnum):
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    BOTH = "both"


class ImpactSeverity(StrEnum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class GraphQueryLimits:
    maximum_depth: int = DEFAULT_MAX_DEPTH
    maximum_nodes: int = DEFAULT_MAX_NODES
    maximum_edges: int = DEFAULT_MAX_EDGES
    maximum_paths: int = DEFAULT_MAX_PATHS
    timeout_budget_ms: int = DEFAULT_TIMEOUT_MS

    def __post_init__(self) -> None:
        if self.maximum_depth < 1 or self.maximum_depth > HARD_MAX_DEPTH:
            raise GraphAnalysisLimitError(
                f"maximum_depth must be between 1 and {HARD_MAX_DEPTH}",
                reason_code="max_depth_exceeded",
            )
        if self.maximum_nodes < 1 or self.maximum_nodes > HARD_MAX_NODES:
            raise GraphAnalysisLimitError(
                f"maximum_nodes must be between 1 and {HARD_MAX_NODES}",
                reason_code="max_nodes_exceeded",
            )
        if self.maximum_edges < 1 or self.maximum_edges > HARD_MAX_EDGES:
            raise GraphAnalysisLimitError(
                f"maximum_edges must be between 1 and {HARD_MAX_EDGES}",
                reason_code="max_edges_exceeded",
            )
        if self.maximum_paths < 1 or self.maximum_paths > HARD_MAX_PATHS:
            raise GraphAnalysisLimitError(
                f"maximum_paths must be between 1 and {HARD_MAX_PATHS}",
                reason_code="max_paths_exceeded",
            )
        if self.timeout_budget_ms < 1 or self.timeout_budget_ms > 60_000:
            raise GraphAnalysisLimitError(
                "timeout_budget_ms must be between 1 and 60000",
                reason_code="timeout_budget_invalid",
            )


@dataclass(frozen=True, slots=True)
class GraphQueryScope:
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId


@dataclass(frozen=True, slots=True)
class GraphQueryContext:
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    graph_id: KnowledgeGraphId
    graph_version: GraphVersion
    engineering_snapshot_id: EngineeringSnapshotId
    requested_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def scope(self) -> GraphQueryScope:
        return GraphQueryScope(
            organization_id=self.organization_id,
            workspace_id=self.workspace_id,
            repository_id=self.repository_id,
        )


@dataclass(frozen=True, slots=True)
class GraphQueryDiagnostic:
    code: str
    message: str
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GraphQueryTrace:
    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    rules_applied: tuple[str, ...]
    limits: GraphQueryLimits
    diagnostics: tuple[GraphQueryDiagnostic, ...] = ()
