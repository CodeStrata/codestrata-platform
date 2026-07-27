"""Application tests for Engineering Knowledge Graph projection."""

from __future__ import annotations

import ast
from pathlib import Path

from codestrata_platform.application.knowledge_graph.commands import BuildKnowledgeGraphCommand
from codestrata_platform.application.knowledge_graph.projection import (
    create_pending_graph,
    project_snapshot_into_graph,
)
from codestrata_platform.application.knowledge_graph.queries import (
    FindGraphPathQuery,
    GetLatestRepositoryGraphQuery,
    GetNodeNeighborsQuery,
    ListGraphNodesQuery,
)
from codestrata_platform.application.knowledge_graph.services import (
    EngineeringGraphProjectionService,
    knowledge_graph_auto_project_enabled,
)
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering import (
    EngineeringCategory,
    EngineeringEvidence,
    EngineeringFinding,
    EngineeringMetric,
    EngineeringMetricKind,
    EngineeringRecommendation,
    EngineeringRelationship,
    EngineeringRelationshipType,
    EngineeringSeverity,
    EngineeringSnapshot,
    EngineeringTechnology,
    EvidenceKind,
)
from codestrata_platform.domain.engineering.ids import (
    EngineeringEvidenceId,
    EngineeringFindingId,
    EngineeringMetricId,
    EngineeringRecommendationId,
    EngineeringRelationshipId,
    EngineeringSnapshotId,
    EngineeringTechnologyId,
)
from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId, KnowledgeGraphId
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.memory import (
    InMemoryEngineeringSnapshotRepository,
    InMemoryKnowledgeGraphRepository,
)


def _published_snapshot() -> EngineeringSnapshot:
    snapshot = EngineeringSnapshot.create(
        organization_id=OrganizationId("org:1"),
        workspace_id=WorkspaceId("workspace:1"),
        repository_id=RepositoryId("repo:1"),
        assessment_id=AssessmentId("assessment:1"),
        assessment_intelligence_id="intelligence:1",
        assessment_revision=1,
        version=1,
        source_artifact_ids=("artifact:1",),
        snapshot_id=EngineeringSnapshotId("eng-snapshot:fixed1"),
    )
    finding_id = EngineeringFindingId("eng-finding:1")
    evidence_id = EngineeringEvidenceId("eng-evidence:1")
    recommendation_id = EngineeringRecommendationId("eng-recommendation:1")
    technology = EngineeringTechnology(
        technology_id=EngineeringTechnologyId("eng-tech:1"),
        canonical_key="docker",
        display_name="Docker",
        category=EngineeringCategory.CLOUD,
    )
    finding = EngineeringFinding(
        finding_id=finding_id,
        source_finding_id="finding:1",
        category=EngineeringCategory.SECURITY,
        severity=EngineeringSeverity.CRITICAL,
        title="Privileged container",
        summary="Runs privileged.",
        rule_id="rule.docker.hardening",
        confidence=0.95,
        evidence_ids=(evidence_id.value,),
    )
    evidence = EngineeringEvidence(
        evidence_id=evidence_id,
        kind=EvidenceKind.FILE,
        reference="deploy/compose.yml",
        line_start=4,
    )
    recommendation = EngineeringRecommendation(
        recommendation_id=recommendation_id,
        source_recommendation_id="recommendation:1",
        title="Drop privileged mode",
        rationale="Remove privileged: true",
        category=EngineeringCategory.SECURITY,
        severity=EngineeringSeverity.HIGH,
        priority="p1",
        related_finding_ids=("finding:1",),
    )
    metric = EngineeringMetric(
        metric_id=EngineeringMetricId("eng-metric:1"),
        name="security.findings.critical",
        kind=EngineeringMetricKind.COUNT,
        value="1",
    )
    relationship = EngineeringRelationship(
        relationship_id=EngineeringRelationshipId("eng-rel:1"),
        relationship_type=EngineeringRelationshipType.USES,
        source_type="repository",
        source_id=snapshot.repository_id.value,
        target_type="technology",
        target_id="docker",
    )
    snapshot.build(
        technologies=(technology,),
        findings=(finding,),
        evidence=(evidence,),
        recommendations=(recommendation,),
        metrics=(metric,),
        relationships=(relationship,),
    )
    snapshot.publish()
    return snapshot


def test_projection_builds_hierarchy_and_ceim_objects() -> None:
    snapshot = _published_snapshot()
    graph = create_pending_graph(
        snapshot,
        graph_version=1,
        projector_version="1.0.0",
        projection_schema_version="1.0",
    )
    graph.begin_projection()
    project_snapshot_into_graph(graph, snapshot)
    graph.complete()

    types = {node.node_type for node in graph.nodes}
    assert GraphNodeType.ORGANIZATION in types
    assert GraphNodeType.TECHNOLOGY in types
    assert GraphNodeType.FINDING in types
    assert GraphNodeType.EVIDENCE in types
    assert GraphNodeType.RECOMMENDATION in types
    assert GraphNodeType.METRIC in types
    assert GraphNodeType.RISK in types
    edge_types = {edge.edge_type for edge in graph.edges}
    assert GraphEdgeType.ORGANIZATION_OWNS_WORKSPACE in edge_types
    assert GraphEdgeType.REPOSITORY_USES_TECHNOLOGY in edge_types
    assert GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE in edge_types
    assert GraphEdgeType.RECOMMENDATION_RESOLVES_FINDING in edge_types


def test_build_is_idempotent_and_queryable() -> None:
    snapshots = InMemoryEngineeringSnapshotRepository()
    graphs = InMemoryKnowledgeGraphRepository()
    snapshot = _published_snapshot()
    snapshots.save(snapshot)
    service = EngineeringGraphProjectionService(graphs=graphs, snapshots=snapshots, queries=graphs)

    first = service.build_knowledge_graph(
        BuildKnowledgeGraphCommand(snapshot_id=snapshot.snapshot_id)
    )
    second = service.build_knowledge_graph(
        BuildKnowledgeGraphCommand(snapshot_id=snapshot.snapshot_id)
    )
    assert first.created is True
    assert second.idempotent is True
    assert first.graph.graph_id == second.graph.graph_id

    latest = service.get_latest_repository_graph(
        GetLatestRepositoryGraphQuery(repository_id=snapshot.repository_id)
    )
    assert latest.graph_id == first.graph.graph_id

    graph_id = KnowledgeGraphId(first.graph.graph_id)
    nodes = service.list_graph_nodes(
        ListGraphNodesQuery(graph_id=graph_id, node_type=GraphNodeType.TECHNOLOGY)
    )
    assert len(nodes) == 1
    assert nodes[0].canonical_id == "docker"

    tech_node_id = GraphNodeId(nodes[0].node_id)
    neighbors = service.get_node_neighbors(
        GetNodeNeighborsQuery(graph_id=graph_id, node_id=tech_node_id)
    )
    assert neighbors

    repo_node = service.list_graph_nodes(
        ListGraphNodesQuery(graph_id=graph_id, node_type=GraphNodeType.REPOSITORY)
    )[0]
    paths = service.find_graph_paths(
        FindGraphPathQuery(
            graph_id=graph_id,
            source_node_id=GraphNodeId(repo_node.node_id),
            target_node_id=tech_node_id,
            max_depth=3,
        )
    )
    assert paths


def test_auto_project_defaults_off(monkeypatch) -> None:
    monkeypatch.delenv("CODESTRATA_KNOWLEDGE_GRAPH_AUTO_PROJECT", raising=False)
    assert knowledge_graph_auto_project_enabled() is False
    monkeypatch.setenv("CODESTRATA_KNOWLEDGE_GRAPH_AUTO_PROJECT", "true")
    assert knowledge_graph_auto_project_enabled() is True


def test_projection_module_avoids_artifact_and_ai_imports() -> None:
    root = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "codestrata_platform"
        / "application"
        / "knowledge_graph"
    )
    forbidden = (
        "codestrata_platform.application.intelligence",
        "codestrata_platform.rag",
        "openai",
        "anthropic",
    )
    for path in root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not any(marker in alias.name for marker in forbidden)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not any(marker in node.module for marker in forbidden)
        lowered = source.lower()
        assert "parse_artifact" not in lowered
        assert "embedding" not in lowered
