"""Domain tests for Engineering Knowledge Graph lifecycle and identity."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.errors import InvalidStateTransitionError
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.errors import GraphInvariantError
from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.identifiers import (
    GraphProjectionKey,
    deterministic_edge_id,
    deterministic_graph_id,
    deterministic_node_id,
)
from codestrata_platform.domain.knowledge_graph.node import GraphNode, GraphProperty
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _pending() -> EngineeringKnowledgeGraph:
    return EngineeringKnowledgeGraph.create_pending(
        graph_id=deterministic_graph_id(
            repository_id="repo:1",
            snapshot_id="snapshot:1",
            snapshot_version=1,
            projector_version="1.0.0",
        ),
        organization_id=OrganizationId("org:1"),
        workspace_id=WorkspaceId("workspace:1"),
        repository_id=RepositoryId("repo:1"),
        assessment_id=AssessmentId("assessment:1"),
        engineering_snapshot_id=EngineeringSnapshotId("eng-snapshot:1"),
        engineering_snapshot_version=1,
        intelligence_revision=1,
        graph_version=1,
        projection_key=GraphProjectionKey.from_parts(
            engineering_snapshot_id="eng-snapshot:1",
            engineering_snapshot_version=1,
            projection_schema_version="1.0",
            projector_version="1.0.0",
        ),
        projection_schema_version="1.0",
        projector_version="1.0.0",
    )


def _node(canonical_id: str, node_type: GraphNodeType = GraphNodeType.TECHNOLOGY) -> GraphNode:
    return GraphNode(
        node_id=deterministic_node_id(
            snapshot_id="eng-snapshot:1",
            node_type=node_type.value,
            canonical_id=canonical_id,
        ),
        node_type=node_type,
        canonical_type=node_type.value.lower(),
        canonical_id=canonical_id,
        display_name=canonical_id,
        properties=GraphProperty(values={"name": canonical_id}),
    )


def test_deterministic_identities_are_stable() -> None:
    first = deterministic_node_id(
        snapshot_id="snap:1",
        node_type="technology",
        canonical_id="docker",
    )
    second = deterministic_node_id(
        snapshot_id="snap:1",
        node_type="technology",
        canonical_id="docker",
    )
    assert first == second
    edge_a = deterministic_edge_id(
        graph_id="eng-graph:1",
        source_node_id=first.value,
        edge_type=GraphEdgeType.REPOSITORY_USES_TECHNOLOGY.value,
        target_node_id=second.value,
    )
    edge_b = deterministic_edge_id(
        graph_id="eng-graph:1",
        source_node_id=first.value,
        edge_type=GraphEdgeType.REPOSITORY_USES_TECHNOLOGY.value,
        target_node_id=second.value,
    )
    assert edge_a == edge_b


def test_graph_lifecycle_and_immutability() -> None:
    graph = _pending()
    graph.begin_projection()
    org = _node("org:1", GraphNodeType.ORGANIZATION)
    workspace = _node("workspace:1", GraphNodeType.WORKSPACE)
    graph.add_node(org)
    graph.add_node(workspace)
    graph.add_edge(
        GraphEdge(
            edge_id=deterministic_edge_id(
                graph_id=graph.graph_id.value,
                source_node_id=org.node_id.value,
                edge_type=GraphEdgeType.ORGANIZATION_OWNS_WORKSPACE.value,
                target_node_id=workspace.node_id.value,
            ),
            source_node_id=org.node_id,
            target_node_id=workspace.node_id,
            edge_type=GraphEdgeType.ORGANIZATION_OWNS_WORKSPACE,
        )
    )
    graph.complete()
    with pytest.raises(InvalidStateTransitionError):
        graph.add_node(_node("extra"))
    graph.supersede()
    assert graph.status.value == "superseded"


def test_idempotent_edge_and_duplicate_node_conflict() -> None:
    graph = _pending()
    graph.begin_projection()
    node = _node("docker")
    graph.add_node(node)
    graph.add_node(node)
    conflict = GraphNode(
        node_id=node.node_id,
        node_type=GraphNodeType.TECHNOLOGY,
        canonical_type="technology",
        canonical_id="docker",
        display_name="Docker Changed",
    )
    with pytest.raises(GraphInvariantError):
        graph.add_node(conflict)

    other = _node("kubernetes")
    graph.add_node(other)
    edge = GraphEdge(
        edge_id=deterministic_edge_id(
            graph_id=graph.graph_id.value,
            source_node_id=node.node_id.value,
            edge_type=GraphEdgeType.COMPONENT_USES_TECHNOLOGY.value,
            target_node_id=other.node_id.value,
        ),
        source_node_id=node.node_id,
        target_node_id=other.node_id,
        edge_type=GraphEdgeType.COMPONENT_USES_TECHNOLOGY,
    )
    graph.add_edge(edge)
    graph.add_edge(edge)
    assert len(graph.edges) == 1


def test_invalid_edge_reference_and_self_reference() -> None:
    graph = _pending()
    graph.begin_projection()
    node = _node("docker")
    missing = _node("missing")
    graph.add_node(node)
    with pytest.raises(GraphInvariantError):
        graph.add_edge(
            GraphEdge(
                edge_id=deterministic_edge_id(
                    graph_id=graph.graph_id.value,
                    source_node_id=node.node_id.value,
                    edge_type=GraphEdgeType.REPOSITORY_USES_TECHNOLOGY.value,
                    target_node_id=missing.node_id.value,
                ),
                source_node_id=node.node_id,
                target_node_id=missing.node_id,
                edge_type=GraphEdgeType.REPOSITORY_USES_TECHNOLOGY,
            )
        )
    with pytest.raises(GraphInvariantError):
        graph.add_edge(
            GraphEdge(
                edge_id=deterministic_edge_id(
                    graph_id=graph.graph_id.value,
                    source_node_id=node.node_id.value,
                    edge_type=GraphEdgeType.REPOSITORY_USES_TECHNOLOGY.value,
                    target_node_id=node.node_id.value,
                    discriminator="self",
                ),
                source_node_id=node.node_id,
                target_node_id=node.node_id,
                edge_type=GraphEdgeType.REPOSITORY_USES_TECHNOLOGY,
            )
        )


def test_failed_graph_cannot_complete() -> None:
    graph = _pending()
    graph.begin_projection()
    graph.fail("projection boom")
    with pytest.raises(InvalidStateTransitionError):
        graph.complete()
