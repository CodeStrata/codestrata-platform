"""Graph integrity analysis against persisted nodes and edges."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType

INTEGRITY_VERSION = "1.0.0"

HIERARCHY_TYPES = frozenset(
    {
        GraphNodeType.ORGANIZATION,
        GraphNodeType.WORKSPACE,
        GraphNodeType.REPOSITORY,
        GraphNodeType.ASSESSMENT,
        GraphNodeType.ENGINEERING_SNAPSHOT,
    }
)


class GraphIntegrityIssueType(StrEnum):
    DANGLING_EDGE_REFERENCE = "dangling_edge_reference"
    DUPLICATE_CANONICAL_NODE = "duplicate_canonical_node"
    CONFLICTING_CANONICAL_PROPERTIES = "conflicting_canonical_properties"
    UNSUPPORTED_EDGE_TYPE = "unsupported_edge_type"
    CROSS_TENANT_EDGE = "cross_tenant_edge"
    DISCONNECTED_HIERARCHY_NODE = "disconnected_hierarchy_node"
    MISSING_REPOSITORY_HIERARCHY = "missing_repository_hierarchy"
    INCOMPLETE_SNAPSHOT_HIERARCHY = "incomplete_snapshot_hierarchy"
    INVALID_SUPERSESSION_LINK = "invalid_supersession_link"
    ACTIVE_GRAPH_INCONSISTENCY = "active_graph_inconsistency"
    MISSING_CANONICAL_REFERENCE = "missing_canonical_reference"
    MISSING_SOURCE_REFERENCE = "missing_source_reference"


class GraphIntegritySeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class GraphIntegrityIssue:
    issue_type: GraphIntegrityIssueType
    severity: GraphIntegritySeverity
    message: str
    node_ids: tuple[str, ...] = ()
    edge_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GraphIntegrityReport:
    integrity_version: str
    issues: tuple[GraphIntegrityIssue, ...]
    issue_count: int
    critical_issue_count: int
    passed: bool


def validate_graph_integrity(graph: EngineeringKnowledgeGraph) -> GraphIntegrityReport:
    nodes = graph.nodes
    edges = graph.edges
    node_ids = {item.node_id.value for item in nodes}
    issues: list[GraphIntegrityIssue] = []

    for edge in edges:
        if edge.source_node_id.value not in node_ids or edge.target_node_id.value not in node_ids:
            issues.append(
                GraphIntegrityIssue(
                    issue_type=GraphIntegrityIssueType.DANGLING_EDGE_REFERENCE,
                    severity=GraphIntegritySeverity.CRITICAL,
                    message="Edge references a missing node",
                    edge_ids=(edge.edge_id.value,),
                    node_ids=(edge.source_node_id.value, edge.target_node_id.value),
                )
            )
        try:
            GraphEdgeType(edge.edge_type.value)
        except ValueError:
            issues.append(
                GraphIntegrityIssue(
                    issue_type=GraphIntegrityIssueType.UNSUPPORTED_EDGE_TYPE,
                    severity=GraphIntegritySeverity.ERROR,
                    message=f"Unsupported edge type {edge.edge_type}",
                    edge_ids=(edge.edge_id.value,),
                )
            )

    by_canonical: dict[tuple[str, str], list[GraphNode]] = {}
    for node in nodes:
        key = (node.canonical_type, node.canonical_id)
        by_canonical.setdefault(key, []).append(node)
        if not node.canonical_type or not node.canonical_id:
            issues.append(
                GraphIntegrityIssue(
                    issue_type=GraphIntegrityIssueType.MISSING_CANONICAL_REFERENCE,
                    severity=GraphIntegritySeverity.ERROR,
                    message="Node is missing canonical identity",
                    node_ids=(node.node_id.value,),
                )
            )
        if node.node_type not in HIERARCHY_TYPES and node.source_reference is None:
            issues.append(
                GraphIntegrityIssue(
                    issue_type=GraphIntegrityIssueType.MISSING_SOURCE_REFERENCE,
                    severity=GraphIntegritySeverity.WARNING,
                    message="Non-hierarchy node lacks source reference",
                    node_ids=(node.node_id.value,),
                )
            )

    for (_ctype, _cid), group in by_canonical.items():
        if len(group) <= 1:
            continue
        props = {tuple(sorted(dict(item.properties.values).items())) for item in group}
        if len(props) > 1:
            issues.append(
                GraphIntegrityIssue(
                    issue_type=GraphIntegrityIssueType.CONFLICTING_CANONICAL_PROPERTIES,
                    severity=GraphIntegritySeverity.ERROR,
                    message="Duplicate canonical nodes have conflicting properties",
                    node_ids=tuple(item.node_id.value for item in group),
                )
            )
        else:
            issues.append(
                GraphIntegrityIssue(
                    issue_type=GraphIntegrityIssueType.DUPLICATE_CANONICAL_NODE,
                    severity=GraphIntegritySeverity.WARNING,
                    message="Duplicate canonical nodes present",
                    node_ids=tuple(item.node_id.value for item in group),
                )
            )

    present_types = {item.node_type for item in nodes}
    for required in HIERARCHY_TYPES:
        if required not in present_types:
            issues.append(
                GraphIntegrityIssue(
                    issue_type=GraphIntegrityIssueType.INCOMPLETE_SNAPSHOT_HIERARCHY,
                    severity=GraphIntegritySeverity.CRITICAL,
                    message=f"Missing required hierarchy node type {required.value}",
                )
            )

    if GraphNodeType.REPOSITORY not in present_types:
        issues.append(
            GraphIntegrityIssue(
                issue_type=GraphIntegrityIssueType.MISSING_REPOSITORY_HIERARCHY,
                severity=GraphIntegritySeverity.CRITICAL,
                message="Repository hierarchy node is missing",
            )
        )

    connected: set[str] = set()
    for edge in edges:
        connected.add(edge.source_node_id.value)
        connected.add(edge.target_node_id.value)
    for node in nodes:
        if node.node_type in HIERARCHY_TYPES and node.node_id.value not in connected:
            issues.append(
                GraphIntegrityIssue(
                    issue_type=GraphIntegrityIssueType.DISCONNECTED_HIERARCHY_NODE,
                    severity=GraphIntegritySeverity.ERROR,
                    message="Hierarchy node is disconnected from the graph",
                    node_ids=(node.node_id.value,),
                )
            )

    for edge in edges:
        if edge.edge_type in {
            GraphEdgeType.GRAPH_SUPERSEDES_GRAPH,
            GraphEdgeType.SNAPSHOT_SUPERSEDES_SNAPSHOT,
        }:
            if edge.source_node_id.value == edge.target_node_id.value:
                issues.append(
                    GraphIntegrityIssue(
                        issue_type=GraphIntegrityIssueType.INVALID_SUPERSESSION_LINK,
                        severity=GraphIntegritySeverity.ERROR,
                        message="Supersession edge is self-referential",
                        edge_ids=(edge.edge_id.value,),
                    )
                )

    critical = sum(
        1 for item in issues if item.severity is GraphIntegritySeverity.CRITICAL
    )
    return GraphIntegrityReport(
        integrity_version=INTEGRITY_VERSION,
        issues=tuple(issues),
        issue_count=len(issues),
        critical_issue_count=critical,
        passed=critical == 0
        and not any(item.severity is GraphIntegritySeverity.ERROR for item in issues),
    )
