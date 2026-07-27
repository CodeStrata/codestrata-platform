"""EngineeringKnowledgeGraph aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.errors import InvalidStateTransitionError, InvalidValueError
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.errors import GraphInvariantError
from codestrata_platform.domain.knowledge_graph.identifiers import (
    GraphProjectionId,
    GraphProjectionKey,
    KnowledgeGraphId,
)
from codestrata_platform.domain.knowledge_graph.lifecycle import GraphStatus, GraphVersion
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import ALLOWED_SELF_REFERENCE_EDGES
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(slots=True)
class EngineeringKnowledgeGraph:
    """Deterministic CEIM projection graph for one EngineeringSnapshot."""

    graph_id: KnowledgeGraphId
    projection_id: GraphProjectionId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    assessment_id: AssessmentId
    engineering_snapshot_id: EngineeringSnapshotId
    engineering_snapshot_version: int
    intelligence_revision: int
    graph_version: GraphVersion
    status: GraphStatus
    projection_key: GraphProjectionKey
    projection_schema_version: str
    projector_version: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    audit: AuditInfo
    completed_at: datetime | None = None
    superseded_at: datetime | None = None
    failure_reason: str | None = None
    _version: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        if self.engineering_snapshot_version < 1:
            raise InvalidValueError(
                "engineering_snapshot_version must be >= 1",
                reason_code="invalid_snapshot_version",
            )
        if self.intelligence_revision < 1:
            raise InvalidValueError(
                "intelligence_revision must be >= 1",
                reason_code="invalid_intelligence_revision",
            )
        self.projection_schema_version = self.projection_schema_version.strip()
        self.projector_version = self.projector_version.strip()
        if not self.projection_schema_version or not self.projector_version:
            raise InvalidValueError(
                "projection schema/projector versions must be non-blank",
                reason_code="empty_projection_version",
            )
        self._assert_integrity()

    @classmethod
    def create_pending(
        cls,
        *,
        graph_id: KnowledgeGraphId,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        repository_id: RepositoryId,
        assessment_id: AssessmentId,
        engineering_snapshot_id: EngineeringSnapshotId,
        engineering_snapshot_version: int,
        intelligence_revision: int,
        graph_version: int,
        projection_key: GraphProjectionKey,
        projection_schema_version: str,
        projector_version: str,
        projection_id: GraphProjectionId | None = None,
    ) -> EngineeringKnowledgeGraph:
        return cls(
            graph_id=graph_id,
            projection_id=projection_id or GraphProjectionId.generate(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            repository_id=repository_id,
            assessment_id=assessment_id,
            engineering_snapshot_id=engineering_snapshot_id,
            engineering_snapshot_version=engineering_snapshot_version,
            intelligence_revision=intelligence_revision,
            graph_version=GraphVersion(graph_version),
            status=GraphStatus.PENDING,
            projection_key=projection_key,
            projection_schema_version=projection_schema_version,
            projector_version=projector_version,
            nodes=(),
            edges=(),
            audit=AuditInfo.create(),
        )

    def begin_projection(self) -> None:
        self._require_mutable()
        if self.status is not GraphStatus.PENDING:
            raise InvalidStateTransitionError(
                f"Cannot begin projection from status {self.status.value}",
                reason_code="invalid_begin_projection",
            )
        self.status = GraphStatus.PROJECTING
        self.audit = self.audit.touch()
        self._version += 1

    def add_node(self, node: GraphNode) -> None:
        self._require_projecting()
        existing = {item.node_id.value: item for item in self.nodes}
        prior = existing.get(node.node_id.value)
        if prior is not None:
            if (
                prior.node_type != node.node_type
                or prior.canonical_type != node.canonical_type
                or prior.canonical_id != node.canonical_id
                or prior.display_name != node.display_name
                or dict(prior.properties.values) != dict(node.properties.values)
            ):
                raise GraphInvariantError(
                    f"Conflicting node for id {node.node_id.value}",
                    reason_code="duplicate_node_conflict",
                )
            return
        self.nodes = (*self.nodes, node)
        self.audit = self.audit.touch()
        self._version += 1

    def add_edge(self, edge: GraphEdge) -> None:
        self._require_projecting()
        node_ids = {item.node_id.value for item in self.nodes}
        if edge.source_node_id.value not in node_ids:
            raise GraphInvariantError(
                f"Edge source node missing: {edge.source_node_id.value}",
                reason_code="missing_source_node",
            )
        if edge.target_node_id.value not in node_ids:
            raise GraphInvariantError(
                f"Edge target node missing: {edge.target_node_id.value}",
                reason_code="missing_target_node",
            )
        if (
            edge.source_node_id.value == edge.target_node_id.value
            and edge.edge_type not in ALLOWED_SELF_REFERENCE_EDGES
        ):
            raise GraphInvariantError(
                f"Self-reference not allowed for edge type {edge.edge_type.value}",
                reason_code="self_reference_forbidden",
            )
        for existing in self.edges:
            if existing.edge_id.value == edge.edge_id.value:
                if (
                    existing.source_node_id != edge.source_node_id
                    or existing.target_node_id != edge.target_node_id
                    or existing.edge_type != edge.edge_type
                    or dict(existing.properties.values) != dict(edge.properties.values)
                ):
                    raise GraphInvariantError(
                        f"Conflicting edge for id {edge.edge_id.value}",
                        reason_code="duplicate_edge_conflict",
                    )
                return
        self.edges = (*self.edges, edge)
        self.audit = self.audit.touch()
        self._version += 1

    def complete(self) -> None:
        self._require_projecting()
        self._assert_integrity()
        self.status = GraphStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.failure_reason = None
        self.audit = self.audit.touch()
        self._version += 1

    def fail(self, reason: str) -> None:
        self._require_mutable()
        if self.status not in {GraphStatus.PENDING, GraphStatus.PROJECTING}:
            raise InvalidStateTransitionError(
                f"Cannot fail graph in status {self.status.value}",
                reason_code="invalid_fail_transition",
            )
        compact = reason.strip()
        if not compact:
            raise InvalidValueError(
                "failure reason must be non-blank",
                reason_code="empty_failure_reason",
            )
        self.status = GraphStatus.FAILED
        self.failure_reason = compact[:1000]
        self.nodes = ()
        self.edges = ()
        self.audit = self.audit.touch()
        self._version += 1

    def supersede(self) -> None:
        if self.status is not GraphStatus.COMPLETED:
            raise InvalidStateTransitionError(
                f"Cannot supersede graph in status {self.status.value}",
                reason_code="invalid_supersede_transition",
            )
        self.status = GraphStatus.SUPERSEDED
        self.superseded_at = datetime.now(UTC)
        self.audit = self.audit.touch()
        self._version += 1

    def archive(self) -> None:
        if self.status not in {GraphStatus.COMPLETED, GraphStatus.SUPERSEDED}:
            raise InvalidStateTransitionError(
                f"Cannot archive graph in status {self.status.value}",
                reason_code="invalid_archive_transition",
            )
        self.status = GraphStatus.ARCHIVED
        self.audit = self.audit.touch()
        self._version += 1

    def snapshot(self) -> EngineeringKnowledgeGraph:
        return replace(self)

    def _require_mutable(self) -> None:
        if self.status is GraphStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Completed knowledge graphs are immutable",
                reason_code="graph_immutable",
            )
        if self.status in {GraphStatus.SUPERSEDED, GraphStatus.ARCHIVED, GraphStatus.FAILED}:
            raise InvalidStateTransitionError(
                f"Graph in status {self.status.value} is immutable",
                reason_code="graph_immutable",
            )

    def _require_projecting(self) -> None:
        self._require_mutable()
        if self.status is not GraphStatus.PROJECTING:
            raise InvalidStateTransitionError(
                f"Cannot mutate graph contents in status {self.status.value}",
                reason_code="graph_not_projecting",
            )

    def _assert_integrity(self) -> None:
        node_ids = [item.node_id.value for item in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise GraphInvariantError(
                "Node ids must be unique within a graph",
                reason_code="duplicate_node_id",
            )
        edge_ids = [item.edge_id.value for item in self.edges]
        if len(edge_ids) != len(set(edge_ids)):
            raise GraphInvariantError(
                "Edge ids must be unique within a graph",
                reason_code="duplicate_edge_id",
            )
        known = set(node_ids)
        for edge in self.edges:
            if edge.source_node_id.value not in known or edge.target_node_id.value not in known:
                raise GraphInvariantError(
                    "Edges may only reference nodes in the same graph",
                    reason_code="edge_node_mismatch",
                )
