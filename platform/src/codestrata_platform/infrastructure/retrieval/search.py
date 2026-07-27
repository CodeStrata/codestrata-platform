"""Shared hybrid / lexical / vector ranking helpers for retrieval repositories."""

from __future__ import annotations

import math
import re

from codestrata_platform.application.retrieval.policies import DefaultHybridRetrievalPolicy
from codestrata_platform.domain.retrieval.chunk import RetrievalChunk
from codestrata_platform.domain.retrieval.document import RetrievalDocument
from codestrata_platform.domain.retrieval.identifiers import (
    EmbeddingVector,
    RetrievalIndexId,
    RetrievalResultId,
)
from codestrata_platform.domain.retrieval.index import EngineeringRetrievalIndex
from codestrata_platform.domain.retrieval.query import (
    RetrievalQuery,
    RetrievalScope,
    RetrievalScore,
)
from codestrata_platform.domain.retrieval.result import RetrievalHit, RetrievalSearchResult
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType, RetrievalMode

_TOKEN = re.compile(r"[a-z0-9]+")

_SOURCE_QUALITY = {
    RetrievalContentType.FINDING: 1.0,
    RetrievalContentType.RECOMMENDATION: 0.95,
    RetrievalContentType.TECHNOLOGY: 0.85,
    RetrievalContentType.COMPONENT: 0.85,
    RetrievalContentType.REPOSITORY_SUMMARY: 0.8,
    RetrievalContentType.EVIDENCE: 0.75,
    RetrievalContentType.METRIC: 0.7,
}


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


def lexical_score(query_text: str, chunk_text: str) -> float:
    query_tokens = _tokens(query_text)
    if not query_tokens:
        return 0.0
    chunk_tokens = _tokens(chunk_text)
    if not chunk_tokens:
        return 0.0
    overlap = len(query_tokens & chunk_tokens)
    return min(1.0, overlap / len(query_tokens))


def cosine_similarity(left: EmbeddingVector, right: EmbeddingVector) -> float:
    if left.dimension != right.dimension:
        return 0.0
    dot = sum(a * b for a, b in zip(left.values, right.values, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left.values))
    right_norm = math.sqrt(sum(b * b for b in right.values))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return max(0.0, min(1.0, (dot / (left_norm * right_norm) + 1.0) / 2.0))


def graph_relevance_score(
    chunk: RetrievalChunk,
    query: RetrievalQuery,
) -> float:
    if not query.graph_node_ids:
        return 0.0
    requested = set(query.graph_node_ids)
    matched = requested.intersection(chunk.graph_node_ids)
    if not matched:
        return 0.0
    depth_factor = 1.0 if query.graph_expansion_depth <= 1 else 0.85
    return min(1.0, (len(matched) / max(1, len(requested))) * depth_factor)


def source_quality_score(content_type: RetrievalContentType) -> float:
    return _SOURCE_QUALITY.get(content_type, 0.5)


def matches_filters(
    *,
    document: RetrievalDocument,
    chunk: RetrievalChunk,
    query: RetrievalQuery,
) -> bool:
    if query.content_types and document.content_type not in query.content_types:
        return False
    if query.canonical_types and document.canonical_type not in query.canonical_types:
        return False
    if query.canonical_ids and document.canonical_id not in query.canonical_ids:
        return False
    if query.graph_node_ids:
        # Soft filter for candidate inclusion when depth=0; depth>=1 uses boost.
        if query.graph_expansion_depth == 0 and not set(query.graph_node_ids).intersection(
            chunk.graph_node_ids
        ):
            return False
    if query.severity:
        if document.metadata.get("severity", "").lower() != query.severity.lower():
            return False
    if query.category:
        if document.metadata.get("category", "").lower() != query.category.lower():
            return False
    return True


def search_index(
    index: EngineeringRetrievalIndex,
    query: RetrievalQuery,
    *,
    scope: RetrievalScope,
    query_embedding: EmbeddingVector | None,
    policy: DefaultHybridRetrievalPolicy | None = None,
) -> RetrievalSearchResult:
    if (
        index.organization_id.value != scope.organization_id
        or index.workspace_id.value != scope.workspace_id
        or index.repository_id.value != scope.repository_id
    ):
        return RetrievalSearchResult(hits=(), mode=query.mode.value, top_k=query.top_k)

    hybrid = policy or DefaultHybridRetrievalPolicy()
    documents = {item.document_id.value: item for item in index.documents}
    hits: list[RetrievalHit] = []
    for chunk in index.chunks:
        document = documents.get(chunk.document_id.value)
        if document is None:
            continue
        if not matches_filters(document=document, chunk=chunk, query=query):
            continue
        lex = lexical_score(query.query_text, chunk.text)
        vec = 0.0
        if query_embedding is not None and chunk.embedding is not None:
            vec = cosine_similarity(query_embedding, chunk.embedding)
        graph = graph_relevance_score(chunk, query)
        quality = source_quality_score(document.content_type)

        if query.mode is RetrievalMode.LEXICAL:
            if lex <= 0:
                continue
            score = RetrievalScore(
                lexical_score=lex,
                vector_score=0.0,
                graph_score=graph,
                source_quality_score=quality,
                final_score=round(0.8 * lex + 0.15 * graph + 0.05 * quality, 6),
                policy_version=hybrid.version,
            )
        elif query.mode is RetrievalMode.VECTOR:
            if vec <= 0:
                continue
            score = RetrievalScore(
                lexical_score=0.0,
                vector_score=vec,
                graph_score=graph,
                source_quality_score=quality,
                final_score=round(0.8 * vec + 0.15 * graph + 0.05 * quality, 6),
                policy_version=hybrid.version,
            )
        else:
            score = hybrid.combine(
                lexical_score=lex,
                vector_score=vec,
                graph_score=graph,
                source_quality_score=quality,
            )
            if score.final_score <= 0:
                continue

        if score.final_score < query.minimum_score:
            continue
        digest = chunk.chunk_id.value.replace("retrieval-chunk:", "")[:32]
        hits.append(
            RetrievalHit(
                result_id=RetrievalResultId(f"eng-retrieval-hit:{digest}"),
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                content_type=document.content_type,
                canonical_type=document.canonical_type,
                canonical_id=document.canonical_id,
                title=document.title,
                text=chunk.text,
                score=score,
                source_references=chunk.source_references
                if query.include_source_references
                else (),
                graph_node_ids=chunk.graph_node_ids,
                graph_edge_ids=chunk.graph_edge_ids,
            )
        )

    hits.sort(
        key=lambda item: (
            -item.score.final_score,
            item.chunk_id.value,
            item.document_id.value,
        )
    )
    return RetrievalSearchResult(
        hits=tuple(hits[: query.top_k]),
        mode=query.mode.value,
        top_k=query.top_k,
    )


def assert_completed_index_id(index_id: RetrievalIndexId) -> str:
    return index_id.value
