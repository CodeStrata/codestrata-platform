"""Deterministic EngineeringSnapshot → Knowledge Graph projection stages."""

from __future__ import annotations

from codestrata_platform.domain.engineering import (
    EngineeringRelationshipType,
    EngineeringSnapshot,
    EngineeringSnapshotStatus,
)
from codestrata_platform.domain.engineering.enums import EngineeringSeverity
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.identifiers import (
    GraphProjectionKey,
    deterministic_edge_id,
    deterministic_graph_id,
    deterministic_node_id,
)
from codestrata_platform.domain.knowledge_graph.node import (
    GraphNode,
    GraphProperty,
    GraphSourceReference,
)
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType

DEFAULT_PROJECTOR_VERSION = "1.0.0"
DEFAULT_PROJECTION_SCHEMA_VERSION = "1.0"


def build_projection_key(
    snapshot: EngineeringSnapshot,
    *,
    projector_version: str,
    projection_schema_version: str,
) -> GraphProjectionKey:
    return GraphProjectionKey.from_parts(
        engineering_snapshot_id=snapshot.snapshot_id.value,
        engineering_snapshot_version=snapshot.version.value,
        projection_schema_version=projection_schema_version,
        projector_version=projector_version,
    )


def project_snapshot_into_graph(
    graph: EngineeringKnowledgeGraph,
    snapshot: EngineeringSnapshot,
) -> None:
    """Run all deterministic projection stages against an open graph."""

    if snapshot.status is not EngineeringSnapshotStatus.PUBLISHED:
        raise ValueError("snapshot_not_published")

    node_index: dict[tuple[str, str], GraphNode] = {}

    def _add(node: GraphNode) -> GraphNode:
        graph.add_node(node)
        node_index[(node.canonical_type, node.canonical_id)] = node
        return node

    def _edge(
        *,
        edge_type: GraphEdgeType,
        source: GraphNode,
        target: GraphNode,
        discriminator: str = "",
    ) -> None:
        graph.add_edge(
            GraphEdge(
                edge_id=deterministic_edge_id(
                    graph_id=graph.graph_id.value,
                    source_node_id=source.node_id.value,
                    edge_type=edge_type.value,
                    target_node_id=target.node_id.value,
                    discriminator=discriminator,
                ),
                source_node_id=source.node_id,
                target_node_id=target.node_id,
                edge_type=edge_type,
            )
        )

    snapshot_id = snapshot.snapshot_id.value

    # Stage 1 — ownership hierarchy
    org = _add(
        _node(
            snapshot_id,
            GraphNodeType.ORGANIZATION,
            "organization",
            snapshot.organization_id.value,
            snapshot.organization_id.value,
        )
    )
    workspace = _add(
        _node(
            snapshot_id,
            GraphNodeType.WORKSPACE,
            "workspace",
            snapshot.workspace_id.value,
            snapshot.workspace_id.value,
        )
    )
    repository = _add(
        _node(
            snapshot_id,
            GraphNodeType.REPOSITORY,
            "repository",
            snapshot.repository_id.value,
            snapshot.repository_id.value,
        )
    )
    assessment = _add(
        _node(
            snapshot_id,
            GraphNodeType.ASSESSMENT,
            "assessment",
            snapshot.assessment_id.value,
            snapshot.assessment_id.value,
        )
    )
    snapshot_node = _add(
        _node(
            snapshot_id,
            GraphNodeType.ENGINEERING_SNAPSHOT,
            "engineering_snapshot",
            snapshot.snapshot_id.value,
            snapshot.snapshot_id.value,
            properties={
                "version": snapshot.version.value,
                "assessment_revision": snapshot.assessment_revision,
            },
        )
    )
    _edge(
        edge_type=GraphEdgeType.ORGANIZATION_OWNS_WORKSPACE,
        source=org,
        target=workspace,
    )
    _edge(
        edge_type=GraphEdgeType.WORKSPACE_CONTAINS_REPOSITORY,
        source=workspace,
        target=repository,
    )
    _edge(
        edge_type=GraphEdgeType.REPOSITORY_HAS_ASSESSMENT,
        source=repository,
        target=assessment,
    )
    _edge(
        edge_type=GraphEdgeType.ASSESSMENT_PRODUCES_SNAPSHOT,
        source=assessment,
        target=snapshot_node,
    )

    # Stage 2 — technologies
    technology_nodes: dict[str, GraphNode] = {}
    for technology in snapshot.technologies:
        node = _add(
            _node(
                snapshot_id,
                GraphNodeType.TECHNOLOGY,
                "technology",
                technology.canonical_key,
                technology.display_name,
                properties={"category": technology.category.value},
            )
        )
        technology_nodes[technology.canonical_key] = node
        _edge(
            edge_type=GraphEdgeType.REPOSITORY_USES_TECHNOLOGY,
            source=repository,
            target=node,
        )

    # Stage 3 — components
    component_nodes: dict[str, GraphNode] = {}
    for component in snapshot.components:
        node = _add(
            _node(
                snapshot_id,
                GraphNodeType.COMPONENT,
                "component",
                component.component_id.value,
                component.name,
                properties={
                    "kind": component.kind,
                    **(
                        {"path_reference": component.path_reference}
                        if component.path_reference
                        else {}
                    ),
                },
            )
        )
        component_nodes[component.component_id.value] = node
        _edge(
            edge_type=GraphEdgeType.REPOSITORY_HAS_COMPONENT,
            source=repository,
            target=node,
        )

    # Stage 4 — findings and risks
    finding_nodes: dict[str, GraphNode] = {}
    category_nodes: dict[str, GraphNode] = {}
    for finding in snapshot.findings:
        node = _add(
            _node(
                snapshot_id,
                GraphNodeType.FINDING,
                "finding",
                finding.source_finding_id,
                finding.title,
                properties={
                    "severity": finding.severity.value,
                    "category": finding.category.value,
                    "rule_id": finding.rule_id,
                    "confidence": finding.confidence,
                },
            )
        )
        finding_nodes[finding.source_finding_id] = node
        finding_nodes[finding.finding_id.value] = node
        _edge(
            edge_type=GraphEdgeType.REPOSITORY_HAS_FINDING,
            source=repository,
            target=node,
        )
        category_key = finding.category.value
        if category_key not in category_nodes:
            category_nodes[category_key] = _add(
                _node(
                    snapshot_id,
                    GraphNodeType.CATEGORY,
                    "category",
                    category_key,
                    category_key,
                )
            )
        _edge(
            edge_type=GraphEdgeType.FINDING_CLASSIFIED_AS_CATEGORY,
            source=node,
            target=category_nodes[category_key],
        )
        if finding.severity in {
            EngineeringSeverity.MEDIUM,
            EngineeringSeverity.HIGH,
            EngineeringSeverity.CRITICAL,
        }:
            risk = _add(
                _node(
                    snapshot_id,
                    GraphNodeType.RISK,
                    "risk",
                    f"risk:{finding.source_finding_id}",
                    finding.title,
                    properties={"severity": finding.severity.value},
                )
            )
            _edge(
                edge_type=GraphEdgeType.FINDING_ASSOCIATED_WITH_RISK,
                source=node,
                target=risk,
            )
        for component_id in finding.component_ids:
            component = component_nodes.get(component_id)
            if component is not None:
                _edge(
                    edge_type=GraphEdgeType.COMPONENT_HAS_FINDING,
                    source=component,
                    target=node,
                )

    # Stage 5 — evidence
    evidence_nodes: dict[str, GraphNode] = {}
    for evidence in snapshot.evidence:
        node = _add(
            _node(
                snapshot_id,
                GraphNodeType.EVIDENCE,
                "evidence",
                evidence.evidence_id.value,
                evidence.reference,
                properties={
                    "kind": evidence.kind.value,
                    **(
                        {"line_start": evidence.line_start}
                        if evidence.line_start is not None
                        else {}
                    ),
                    **({"line_end": evidence.line_end} if evidence.line_end is not None else {}),
                },
            )
        )
        evidence_nodes[evidence.evidence_id.value] = node

    for finding in snapshot.findings:
        finding_node = finding_nodes.get(finding.source_finding_id)
        if finding_node is None:
            continue
        for evidence_id in finding.evidence_ids:
            evidence_node = evidence_nodes.get(evidence_id)
            if evidence_node is None:
                continue
            _edge(
                edge_type=GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE,
                source=finding_node,
                target=evidence_node,
            )

    # Stage 6 — recommendations
    recommendation_nodes: dict[str, GraphNode] = {}
    for recommendation in snapshot.recommendations:
        node = _add(
            _node(
                snapshot_id,
                GraphNodeType.RECOMMENDATION,
                "recommendation",
                recommendation.source_recommendation_id,
                recommendation.title,
                properties={
                    "priority": recommendation.priority,
                    "severity": recommendation.severity.value,
                    "category": recommendation.category.value,
                },
            )
        )
        recommendation_nodes[recommendation.source_recommendation_id] = node
        _edge(
            edge_type=GraphEdgeType.REPOSITORY_HAS_RECOMMENDATION,
            source=repository,
            target=node,
        )
        for related in recommendation.related_finding_ids:
            finding_node = finding_nodes.get(related)
            if finding_node is None:
                continue
            _edge(
                edge_type=GraphEdgeType.RECOMMENDATION_RESOLVES_FINDING,
                source=node,
                target=finding_node,
            )

    # Stage 7 — metrics and tags
    for metric in snapshot.metrics:
        node = _add(
            _node(
                snapshot_id,
                GraphNodeType.METRIC,
                "metric",
                metric.name,
                metric.name,
                properties={
                    "kind": metric.kind.value,
                    "value": metric.value,
                    **({"unit": metric.unit} if metric.unit else {}),
                },
            )
        )
        _edge(
            edge_type=GraphEdgeType.REPOSITORY_HAS_METRIC,
            source=repository,
            target=node,
        )

    for tag in snapshot.tags:
        node = _add(
            _node(
                snapshot_id,
                GraphNodeType.TAG,
                "tag",
                tag.name,
                tag.name,
            )
        )
        for finding in snapshot.findings:
            if finding.category.value == tag.name:
                finding_node = finding_nodes.get(finding.source_finding_id)
                if finding_node is not None:
                    _edge(
                        edge_type=GraphEdgeType.FINDING_TAGGED_WITH,
                        source=finding_node,
                        target=node,
                    )

    # Stage 8 — CEIM relationships (only supported mappings)
    for relationship in snapshot.relationships:
        edge_type = _map_ceim_relationship(relationship)
        if edge_type is None:
            continue
        source = _resolve_ceim_endpoint(
            relationship.source_type,
            relationship.source_id,
            repository=repository,
            finding_nodes=finding_nodes,
            recommendation_nodes=recommendation_nodes,
            technology_nodes=technology_nodes,
            component_nodes=component_nodes,
            evidence_nodes=evidence_nodes,
        )
        target = _resolve_ceim_endpoint(
            relationship.target_type,
            relationship.target_id,
            repository=repository,
            finding_nodes=finding_nodes,
            recommendation_nodes=recommendation_nodes,
            technology_nodes=technology_nodes,
            component_nodes=component_nodes,
            evidence_nodes=evidence_nodes,
        )
        if source is None or target is None:
            continue
        _edge(edge_type=edge_type, source=source, target=target)


def create_pending_graph(
    snapshot: EngineeringSnapshot,
    *,
    graph_version: int,
    projector_version: str,
    projection_schema_version: str,
) -> EngineeringKnowledgeGraph:
    projection_key = build_projection_key(
        snapshot,
        projector_version=projector_version,
        projection_schema_version=projection_schema_version,
    )
    graph_id = deterministic_graph_id(
        repository_id=snapshot.repository_id.value,
        snapshot_id=snapshot.snapshot_id.value,
        snapshot_version=snapshot.version.value,
        projector_version=projector_version,
    )
    return EngineeringKnowledgeGraph.create_pending(
        graph_id=graph_id,
        organization_id=snapshot.organization_id,
        workspace_id=snapshot.workspace_id,
        repository_id=snapshot.repository_id,
        assessment_id=snapshot.assessment_id,
        engineering_snapshot_id=snapshot.snapshot_id,
        engineering_snapshot_version=snapshot.version.value,
        intelligence_revision=snapshot.assessment_revision,
        graph_version=graph_version,
        projection_key=projection_key,
        projection_schema_version=projection_schema_version,
        projector_version=projector_version,
    )


def _node(
    snapshot_id: str,
    node_type: GraphNodeType,
    canonical_type: str,
    canonical_id: str,
    display_name: str,
    *,
    properties: dict[str, object] | None = None,
) -> GraphNode:
    return GraphNode(
        node_id=deterministic_node_id(
            snapshot_id=snapshot_id,
            node_type=node_type.value,
            canonical_id=canonical_id,
        ),
        node_type=node_type,
        canonical_type=canonical_type,
        canonical_id=canonical_id,
        display_name=display_name,
        properties=GraphProperty(values=properties or {}),
        source_reference=GraphSourceReference(
            snapshot_id=snapshot_id,
            canonical_type=canonical_type,
            canonical_id=canonical_id,
        ),
    )


def _map_ceim_relationship(relationship) -> GraphEdgeType | None:
    mapping = {
        (
            EngineeringRelationshipType.USES,
            "repository",
            "technology",
        ): GraphEdgeType.REPOSITORY_USES_TECHNOLOGY,
        (
            EngineeringRelationshipType.HAS,
            "repository",
            "finding",
        ): GraphEdgeType.REPOSITORY_HAS_FINDING,
        (
            EngineeringRelationshipType.SUPPORTED_BY,
            "finding",
            "evidence",
        ): GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE,
        (
            EngineeringRelationshipType.RESOLVES,
            "recommendation",
            "finding",
        ): GraphEdgeType.RECOMMENDATION_RESOLVES_FINDING,
        (
            EngineeringRelationshipType.DEPENDS_ON,
            "component",
            "component",
        ): GraphEdgeType.COMPONENT_DEPENDS_ON_COMPONENT,
        (
            EngineeringRelationshipType.PART_OF,
            "technology",
            "framework",
        ): GraphEdgeType.TECHNOLOGY_PART_OF_FRAMEWORK,
        (
            EngineeringRelationshipType.TAGS,
            "finding",
            "tag",
        ): GraphEdgeType.FINDING_TAGGED_WITH,
    }
    return mapping.get(
        (
            relationship.relationship_type,
            relationship.source_type,
            relationship.target_type,
        )
    )


def _resolve_ceim_endpoint(
    endpoint_type: str,
    endpoint_id: str,
    *,
    repository: GraphNode,
    finding_nodes: dict[str, GraphNode],
    recommendation_nodes: dict[str, GraphNode],
    technology_nodes: dict[str, GraphNode],
    component_nodes: dict[str, GraphNode],
    evidence_nodes: dict[str, GraphNode],
) -> GraphNode | None:
    if endpoint_type == "repository":
        return repository
    if endpoint_type == "finding":
        return finding_nodes.get(endpoint_id)
    if endpoint_type == "recommendation":
        return recommendation_nodes.get(endpoint_id)
    if endpoint_type == "technology":
        return technology_nodes.get(endpoint_id)
    if endpoint_type == "component":
        return component_nodes.get(endpoint_id)
    if endpoint_type == "evidence":
        return evidence_nodes.get(endpoint_id)
    return None
