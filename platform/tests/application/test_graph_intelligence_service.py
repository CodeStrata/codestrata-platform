"""Application and architecture tests for graph intelligence."""

from __future__ import annotations

import ast
from pathlib import Path

from codestrata_platform.application.knowledge_graph.commands import BuildKnowledgeGraphCommand
from codestrata_platform.application.knowledge_graph.intelligence import GraphIntelligenceFacade
from codestrata_platform.application.knowledge_graph.intelligence.queries import (
    AnalyzeFindingImpactQuery,
    GetDependencyAnalysisQuery,
    GetFindingTraceabilityQuery,
    GetGraphCoverageQuery,
    GetGraphRiskSummaryQuery,
    GetRecommendationAnalysisQuery,
    GetRepositoryEngineeringOverviewQuery,
    ValidateGraphIntegrityQuery,
)
from codestrata_platform.application.knowledge_graph.services import (
    EngineeringGraphProjectionService,
)
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering import (
    EngineeringCategory,
    EngineeringEvidence,
    EngineeringFinding,
    EngineeringRecommendation,
    EngineeringSeverity,
    EngineeringSnapshot,
    EngineeringTechnology,
    EvidenceKind,
)
from codestrata_platform.domain.engineering.ids import (
    EngineeringEvidenceId,
    EngineeringFindingId,
    EngineeringRecommendationId,
    EngineeringSnapshotId,
    EngineeringTechnologyId,
)
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphNodeType
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.memory import (
    InMemoryEngineeringSnapshotRepository,
    InMemoryGraphIntelligenceRepository,
    InMemoryKnowledgeGraphRepository,
)


def _published_snapshot() -> EngineeringSnapshot:
    snapshot = EngineeringSnapshot.create(
        organization_id=OrganizationId("org:gi1"),
        workspace_id=WorkspaceId("workspace:gi1"),
        repository_id=RepositoryId("repo:gi1"),
        assessment_id=AssessmentId("assessment:gi1"),
        assessment_intelligence_id="intelligence:gi1",
        assessment_revision=1,
        version=1,
        source_artifact_ids=("artifact:gi1",),
        snapshot_id=EngineeringSnapshotId("eng-snapshot:gi1"),
    )
    evidence_id = EngineeringEvidenceId("eng-evidence:gi1")
    snapshot.build(
        technologies=(
            EngineeringTechnology(
                technology_id=EngineeringTechnologyId("eng-tech:gi1"),
                canonical_key="docker",
                display_name="Docker",
                category=EngineeringCategory.CLOUD,
            ),
        ),
        findings=(
            EngineeringFinding(
                finding_id=EngineeringFindingId("eng-finding:gi1"),
                source_finding_id="finding:gi1",
                category=EngineeringCategory.SECURITY,
                severity=EngineeringSeverity.CRITICAL,
                title="Privileged",
                summary="Privileged container",
                rule_id="rule.docker",
                confidence=0.9,
                evidence_ids=(evidence_id.value,),
            ),
        ),
        evidence=(
            EngineeringEvidence(
                evidence_id=evidence_id,
                kind=EvidenceKind.FILE,
                reference="compose.yml",
                line_start=1,
            ),
        ),
        recommendations=(
            EngineeringRecommendation(
                recommendation_id=EngineeringRecommendationId("eng-rec:gi1"),
                source_recommendation_id="recommendation:gi1",
                title="Drop privileged",
                rationale="Remove privileged mode",
                category=EngineeringCategory.SECURITY,
                severity=EngineeringSeverity.HIGH,
                priority="p1",
                related_finding_ids=("finding:gi1",),
            ),
        ),
    )
    snapshot.publish()
    return snapshot


def _facade():
    snapshots = InMemoryEngineeringSnapshotRepository()
    graphs = InMemoryKnowledgeGraphRepository()
    snapshot = _published_snapshot()
    snapshots.save(snapshot)
    projection = EngineeringGraphProjectionService(
        graphs=graphs,
        snapshots=snapshots,
        queries=graphs,
    )
    built = projection.build_knowledge_graph(
        BuildKnowledgeGraphCommand(snapshot_id=snapshot.snapshot_id)
    )
    facade = GraphIntelligenceFacade(
        graphs=graphs,
        intelligence=InMemoryGraphIntelligenceRepository(graphs),
    )
    return facade, KnowledgeGraphId(built.graph.graph_id), snapshot.repository_id


def test_graph_intelligence_application_flow() -> None:
    facade, graph_id, repository_id = _facade()
    coverage = facade.coverage.get_coverage(GetGraphCoverageQuery(graph_id=graph_id))
    assert coverage.findings_with_evidence.denominator == 1
    assert coverage.findings_with_evidence.percentage == 100.0

    integrity = facade.integrity.validate(ValidateGraphIntegrityQuery(graph_id=graph_id))
    assert integrity.passed is True

    risks = facade.risks.summarize(GetGraphRiskSummaryQuery(graph_id=graph_id))
    assert risks.by_severity.get("critical", 0) >= 1

    recommendations = facade.recommendations.analyze(
        GetRecommendationAnalysisQuery(graph_id=graph_id)
    )
    assert recommendations.total == 1
    assert recommendations.linked_to_findings == 1

    deps = facade.dependencies.analyze(GetDependencyAnalysisQuery(graph_id=graph_id))
    assert deps.maximum_depth >= 0

    overview = facade.overview.get_overview(
        GetRepositoryEngineeringOverviewQuery(repository_id=repository_id)
    )
    assert overview.graph_id == graph_id.value
    assert overview.technology_count >= 1
    assert overview.integrity_passed is True

    # Finding impact + traceability
    graphs = facade.coverage._access._graphs
    graph = graphs.get(graph_id)
    assert graph is not None
    finding = next(item for item in graph.nodes if item.node_type is GraphNodeType.FINDING)
    impact = facade.impact.analyze_finding(
        AnalyzeFindingImpactQuery(graph_id=graph_id, node_id=finding.node_id)
    )
    assert impact.score >= 0
    assert impact.contributing_factors
    assert impact.policy_version

    trace = facade.traceability.finding(
        GetFindingTraceabilityQuery(graph_id=graph_id, node_id=finding.node_id)
    )
    assert "evidence" in trace.related
    assert trace.related["evidence"]


def test_intelligence_architecture_boundaries() -> None:
    root = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "codestrata_platform"
        / "application"
        / "knowledge_graph"
        / "intelligence"
    )
    forbidden = (
        "sqlalchemy",
        "fastapi",
        "codestrata_platform.infrastructure",
        "codestrata_platform.domain.engineering",
        "codestrata_platform.application.intelligence",
        "openai",
        "embedding",
    )
    for path in root.rglob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        for marker in ("parse_artifact", "embedding", "openai"):
            assert marker not in source
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("codestrata_platform.infrastructure")
                assert "sqlalchemy" not in node.module
                assert not node.module.startswith("codestrata_platform.domain.engineering")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "sqlalchemy" not in alias.name
                    assert not alias.name.startswith("codestrata_platform.infrastructure")
    _ = forbidden
