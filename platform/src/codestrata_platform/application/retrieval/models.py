"""Application models for engineering retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.retrieval.index import EngineeringRetrievalIndex
from codestrata_platform.domain.retrieval.lifecycle import RetrievalIndexStatus
from codestrata_platform.domain.retrieval.result import RetrievalHit


@dataclass(frozen=True, slots=True)
class RetrievalIndexSummary:
    index_id: str
    repository_id: str
    assessment_id: str
    engineering_snapshot_id: str
    knowledge_graph_id: str
    index_version: int
    status: RetrievalIndexStatus
    projection_key: str
    embedding_provider_id: str
    embedding_model_id: str
    embedding_dimension: int
    document_count: int
    chunk_count: int
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_aggregate(cls, index: EngineeringRetrievalIndex) -> RetrievalIndexSummary:
        return cls(
            index_id=index.index_id.value,
            repository_id=index.repository_id.value,
            assessment_id=index.assessment_id.value,
            engineering_snapshot_id=index.engineering_snapshot_id.value,
            knowledge_graph_id=index.knowledge_graph_id.value,
            index_version=index.index_version.value,
            status=index.status,
            projection_key=index.projection_key.value,
            embedding_provider_id=index.embedding_provider_id.value,
            embedding_model_id=index.embedding_model_id.value,
            embedding_dimension=index.embedding_dimension.value,
            document_count=len(index.documents),
            chunk_count=len(index.chunks),
            created_at=index.audit.created_at.value,
            completed_at=index.completed_at,
        )


@dataclass(frozen=True, slots=True)
class RetrievalIndexDetails(RetrievalIndexSummary):
    organization_id: str
    workspace_id: str
    engineering_snapshot_version: int
    knowledge_graph_version: int
    retrieval_schema_version: str
    chunking_policy_version: str
    failure_reason: str | None
    created: bool | None = None
    idempotent: bool | None = None

    @classmethod
    def from_aggregate(cls, index: EngineeringRetrievalIndex) -> RetrievalIndexDetails:
        summary = RetrievalIndexSummary.from_aggregate(index)
        return cls(
            index_id=summary.index_id,
            repository_id=summary.repository_id,
            assessment_id=summary.assessment_id,
            engineering_snapshot_id=summary.engineering_snapshot_id,
            knowledge_graph_id=summary.knowledge_graph_id,
            index_version=summary.index_version,
            status=summary.status,
            projection_key=summary.projection_key,
            embedding_provider_id=summary.embedding_provider_id,
            embedding_model_id=summary.embedding_model_id,
            embedding_dimension=summary.embedding_dimension,
            document_count=summary.document_count,
            chunk_count=summary.chunk_count,
            created_at=summary.created_at,
            completed_at=summary.completed_at,
            organization_id=index.organization_id.value,
            workspace_id=index.workspace_id.value,
            engineering_snapshot_version=index.engineering_snapshot_version,
            knowledge_graph_version=index.knowledge_graph_version,
            retrieval_schema_version=index.retrieval_schema_version,
            chunking_policy_version=index.chunking_policy_version,
            failure_reason=index.failure_reason,
        )


@dataclass(frozen=True, slots=True)
class RetrievalDocumentSummary:
    document_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    title: str
    summary: str


@dataclass(frozen=True, slots=True)
class RetrievalChunkSummary:
    chunk_id: str
    document_id: str
    ordinal: int
    token_estimate: int
    text: str
    has_embedding: bool


@dataclass(frozen=True, slots=True)
class RetrievalScoreBreakdown:
    lexical_score: float
    vector_score: float
    graph_score: float
    source_quality_score: float
    final_score: float
    policy_version: str


@dataclass(frozen=True, slots=True)
class RetrievalSearchHitModel:
    result_id: str
    chunk_id: str
    document_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    title: str
    text: str
    score: RetrievalScoreBreakdown
    source_references: tuple[str, ...]
    graph_node_ids: tuple[str, ...]

    @classmethod
    def from_hit(cls, hit: RetrievalHit) -> RetrievalSearchHitModel:
        return cls(
            result_id=hit.result_id.value,
            chunk_id=hit.chunk_id.value,
            document_id=hit.document_id.value,
            content_type=hit.content_type.value,
            canonical_type=hit.canonical_type,
            canonical_id=hit.canonical_id,
            title=hit.title,
            text=hit.text,
            score=RetrievalScoreBreakdown(
                lexical_score=hit.score.lexical_score,
                vector_score=hit.score.vector_score,
                graph_score=hit.score.graph_score,
                source_quality_score=hit.score.source_quality_score,
                final_score=hit.score.final_score,
                policy_version=hit.score.policy_version,
            ),
            source_references=tuple(
                f"{item.source_kind}:{item.source_id}" for item in hit.source_references
            ),
            graph_node_ids=hit.graph_node_ids,
        )


@dataclass(frozen=True, slots=True)
class RetrievalSearchResultModel:
    hits: tuple[RetrievalSearchHitModel, ...]
    mode: str
    top_k: int


@dataclass(frozen=True, slots=True)
class RetrievalIndexStatistics:
    index_id: str
    document_count: int
    chunk_count: int
    embedded_chunk_count: int
    content_type_counts: dict[str, int]


@dataclass(frozen=True, slots=True)
class RetrievalBuildResult:
    index: RetrievalIndexDetails
    created: bool
    idempotent: bool
