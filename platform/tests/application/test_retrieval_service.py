"""Application tests for Engineering Retrieval indexing and search."""

from __future__ import annotations

import pytest

from codestrata_platform.application.knowledge_graph.commands import BuildKnowledgeGraphCommand
from codestrata_platform.application.knowledge_graph.services import (
    EngineeringGraphProjectionService,
)
from codestrata_platform.application.retrieval.commands import BuildRetrievalIndexCommand
from codestrata_platform.application.retrieval.context import RetrievalContextAssembler
from codestrata_platform.application.retrieval.policies import retrieval_indexing_enabled
from codestrata_platform.application.retrieval.queries import (
    AssembleRetrievalContextQuery,
    GetRetrievalIndexStatisticsQuery,
    SearchRetrievalIndexQuery,
)
from codestrata_platform.application.retrieval.services import EngineeringRetrievalIndexingService
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
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.document import RetrievalSourceReference
from codestrata_platform.domain.retrieval.identifiers import (
    RetrievalChunkId,
    RetrievalDocumentId,
    RetrievalIndexId,
    RetrievalResultId,
)
from codestrata_platform.domain.retrieval.query import RetrievalQuery, RetrievalScore
from codestrata_platform.domain.retrieval.result import RetrievalHit
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType, RetrievalMode
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.memory import (
    InMemoryEngineeringSnapshotRepository,
    InMemoryKnowledgeGraphRepository,
    InMemoryRetrievalRepository,
)
from codestrata_platform.infrastructure.retrieval.embeddings import DeterministicEmbeddingProvider


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
        rationale="Remove privileged true from compose.",
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


def _services():
    snapshots = InMemoryEngineeringSnapshotRepository()
    graphs = InMemoryKnowledgeGraphRepository()
    embeddings = DeterministicEmbeddingProvider()
    indexes = InMemoryRetrievalRepository(embeddings=embeddings)
    snapshot = _published_snapshot()
    snapshots.save(snapshot)
    graph_service = EngineeringGraphProjectionService(
        graphs=graphs,
        snapshots=snapshots,
        queries=graphs,
    )
    graph_service.build_knowledge_graph(
        BuildKnowledgeGraphCommand(snapshot_id=snapshot.snapshot_id)
    )
    retrieval = EngineeringRetrievalIndexingService(
        indexes=indexes,
        snapshots=snapshots,
        graphs=graphs,
        embeddings=embeddings,
        queries=indexes,
    )
    return retrieval, snapshot


def test_build_index_is_idempotent_for_projection_key() -> None:
    retrieval, snapshot = _services()
    first = retrieval.build_retrieval_index(
        BuildRetrievalIndexCommand(snapshot_id=snapshot.snapshot_id)
    )
    second = retrieval.build_retrieval_index(
        BuildRetrievalIndexCommand(snapshot_id=snapshot.snapshot_id)
    )
    assert first.created is True
    assert second.idempotent is True
    assert first.index.index_id == second.index.index_id
    assert first.index.document_count >= 1
    assert first.index.chunk_count >= 1


def test_hybrid_search_exposes_score_breakdown() -> None:
    retrieval, snapshot = _services()
    built = retrieval.build_retrieval_index(
        BuildRetrievalIndexCommand(snapshot_id=snapshot.snapshot_id)
    )
    result = retrieval.search(
        SearchRetrievalIndexQuery(
            index_id=RetrievalIndexId(built.index.index_id),
            query=RetrievalQuery(
                query_text="privileged container docker",
                mode=RetrievalMode.HYBRID,
                top_k=5,
            ),
        )
    )
    assert result.hits
    hit = result.hits[0]
    assert hit.score.policy_version
    assert hit.score.final_score >= 0
    assert "```" not in hit.text


def test_lexical_and_vector_modes() -> None:
    retrieval, snapshot = _services()
    built = retrieval.build_retrieval_index(
        BuildRetrievalIndexCommand(snapshot_id=snapshot.snapshot_id)
    )
    index_id = RetrievalIndexId(built.index.index_id)
    lexical = retrieval.search(
        SearchRetrievalIndexQuery(
            index_id=index_id,
            query=RetrievalQuery(query_text="Docker technology", mode=RetrievalMode.LEXICAL),
        )
    )
    vector = retrieval.search(
        SearchRetrievalIndexQuery(
            index_id=index_id,
            query=RetrievalQuery(query_text="Docker technology", mode=RetrievalMode.VECTOR),
        )
    )
    assert lexical.hits or vector.hits


def test_context_assembly_is_bounded_and_cited() -> None:
    retrieval, snapshot = _services()
    built = retrieval.build_retrieval_index(
        BuildRetrievalIndexCommand(snapshot_id=snapshot.snapshot_id)
    )
    context = retrieval.assemble_context(
        AssembleRetrievalContextQuery(
            index_id=RetrievalIndexId(built.index.index_id),
            query_text="privileged container",
            top_k=10,
            max_tokens=500,
        )
    )
    assert context.items
    assert context.token_estimate <= 500
    assert context.items[0].citation.chunk_id
    assert context.items[0].citation.source_references


def test_statistics_and_indexing_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CODESTRATA_RETRIEVAL_INDEXING_ENABLED", raising=False)
    assert retrieval_indexing_enabled() is False
    retrieval, snapshot = _services()
    built = retrieval.build_retrieval_index(
        BuildRetrievalIndexCommand(snapshot_id=snapshot.snapshot_id)
    )
    stats = retrieval.statistics(
        GetRetrievalIndexStatisticsQuery(index_id=RetrievalIndexId(built.index.index_id))
    )
    assert stats.chunk_count == stats.embedded_chunk_count
    assert stats.document_count > 0


def test_context_assembler_deduplicates() -> None:
    hit = RetrievalHit(
        result_id=RetrievalResultId("eng-retrieval-hit:abc"),
        chunk_id=RetrievalChunkId("retrieval-chunk:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
        document_id=RetrievalDocumentId("retrieval-doc:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
        content_type=RetrievalContentType.FINDING,
        canonical_type="finding",
        canonical_id="finding:1",
        title="t",
        text="Finding privileged container summary text for assembly.",
        score=RetrievalScore(final_score=0.9),
        source_references=(
            RetrievalSourceReference(source_kind="engineering_finding", source_id="eng-finding:1"),
        ),
    )
    assembler = RetrievalContextAssembler(max_tokens=1000)
    context = assembler.assemble((hit, hit))
    assert len(context.items) == 1


def test_deterministic_embeddings_repeatable() -> None:
    provider = DeterministicEmbeddingProvider()
    assert provider.embed_text("alpha").values == provider.embed_text("alpha").values
    assert provider.dimension().value == 384
    batch = provider.embed_batch(("a", "b"))
    assert len(batch) == 2
