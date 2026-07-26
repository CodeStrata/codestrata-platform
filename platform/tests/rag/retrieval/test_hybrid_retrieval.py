"""Tests for hybrid / lexical / vector retrieval (Phase 5.9)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from codestrata.config.settings import KnowledgeEmbeddingSettings, KnowledgeRetrievalSettings
from codestrata_platform.rag.application.retrieval import RepositoryRetriever
from codestrata_platform.rag.application.retrieval.fusion import reciprocal_rank_fusion
from codestrata_platform.rag.application.retrieval.lexical import lexical_search, tokenize
from codestrata_platform.rag.domain import (
    RetrievalRequest,
    RetrievalScope,
    RetrievalStatus,
    VectorRecord,
)
from codestrata_platform.rag.domain.vector import VectorSearchResult
from codestrata_platform.rag.embedding import DeterministicEmbeddingProvider
from codestrata_platform.rag.vector_store import InMemoryVectorStore


def _scope(**kwargs: str) -> RetrievalScope:
    base = {"tenant_id": "tenant-a", "repository_id": "repo-a"}
    base.update(kwargs)
    return RetrievalScope(**base)  # type: ignore[arg-type]


def _record(
    entity_id: str,
    text: str,
    *,
    tenant_id: str = "tenant-a",
    repository_id: str = "repo-a",
    scan_id: str = "scan-a",
    **extra: object,
) -> VectorRecord:
    provider = DeterministicEmbeddingProvider(dimension=8)
    meta: dict[str, object] = {
        "tenant_id": tenant_id,
        "repository_id": repository_id,
        "scan_id": scan_id,
        "document_id": f"kd:{entity_id}",
        "chunk_id": f"kc:{entity_id}",
        "chunk_sequence": 0,
        "content_hash": f"hash-{entity_id}",
        "embedding_provider": "deterministic",
        "embedding_model": "deterministic-test-embedding",
        "embedding_model_version": "1.0.0",
        "embedding_dimension": 8,
        **extra,
    }
    return VectorRecord.create(
        entity_id=entity_id,
        embedding=list(provider.embed_text(text).embedding),
        metadata=meta,
        text=text,
    )


def _retriever(
    store: InMemoryVectorStore,
    *,
    mode: str = "vector",
    vector_weight: float = 1.0,
    lexical_weight: float = 1.0,
    embedding: DeterministicEmbeddingProvider | MagicMock | None = None,
) -> RepositoryRetriever:
    provider = embedding or DeterministicEmbeddingProvider(dimension=8)
    return RepositoryRetriever(
        embedding_provider=provider,  # type: ignore[arg-type]
        vector_store=store,
        retrieval_settings=KnowledgeRetrievalSettings(
            enabled=True,
            mode=mode,
            vector_weight=vector_weight,
            lexical_weight=lexical_weight,
            candidate_limit=20,
            top_k=5,
        ),
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True,
            provider="deterministic",
            dimension=8,
        ),
    )


def test_tokenize_stable() -> None:
    assert tokenize("Hello, World!") == ("hello", "world")


def test_vector_only_mode() -> None:
    store = InMemoryVectorStore()
    store.upsert(
        [
            _record("owners", "OwnersController handles pet owners"),
            _record("visits", "VisitsController schedules clinic visits"),
        ]
    )
    retriever = _retriever(store, mode="vector")
    result = retriever.retrieve(
        RetrievalRequest(query="OwnersController pet owners", scope=_scope())
    )
    assert result.status in {RetrievalStatus.SUCCESS, RetrievalStatus.PARTIAL}
    assert result.coverage.retrieval_mode == "vector"
    assert result.coverage.vector_candidates >= 1
    assert result.coverage.lexical_candidates == 0
    assert any(d.code == "retrieval_mode" and d.message == "vector" for d in result.diagnostics)


def test_lexical_only_without_embeddings() -> None:
    store = InMemoryVectorStore()
    store.upsert(
        [
            _record("owners", "OwnersController handles pet owners"),
            _record("db", "Database migration scripts for schema"),
        ]
    )
    embedder = MagicMock()
    embedder.model_identity.return_value = DeterministicEmbeddingProvider(
        dimension=8
    ).model_identity()
    embedder.embed_text.side_effect = RuntimeError("embeddings must not be called")
    retriever = _retriever(store, mode="lexical", embedding=embedder)
    result = retriever.retrieve(
        RetrievalRequest(query="OwnersController pet owners", scope=_scope())
    )
    assert result.status in {RetrievalStatus.SUCCESS, RetrievalStatus.PARTIAL}
    assert result.coverage.retrieval_mode == "lexical"
    assert result.coverage.vector_candidates == 0
    assert result.coverage.lexical_candidates >= 1
    assert result.context is not None
    assert any("OwnersController" in (h.content or "") for h in result.context.hits)
    embedder.embed_text.assert_not_called()


def test_hybrid_mode_and_deterministic_fusion() -> None:
    store = InMemoryVectorStore()
    store.upsert(
        [
            _record("a", "spring petclinic owners controller"),
            _record("b", "unrelated database driver configuration"),
            _record("c", "owners page thymeleaf template"),
        ]
    )
    retriever = _retriever(store, mode="hybrid")
    left = retriever.retrieve(
        RetrievalRequest(query="owners controller", scope=_scope())
    )
    right = retriever.retrieve(
        RetrievalRequest(query="owners controller", scope=_scope())
    )
    assert left.fingerprint == right.fingerprint
    assert left.coverage.retrieval_mode == "hybrid"
    assert left.coverage.vector_candidates >= 1
    assert left.coverage.lexical_candidates >= 1
    assert left.coverage.fused_candidates >= 1
    assert [h.record_id for h in left.context.hits] == [
        h.record_id for h in right.context.hits
    ]


def test_duplicate_removal_across_retrievers() -> None:
    record = _record("same", "unique owners controller evidence")
    vector_hits = (
        VectorSearchResult(record_id=record.record_id, score=0.9, record=record),
    )
    lexical_hits = (
        VectorSearchResult(record_id=record.record_id, score=0.8, record=record),
    )
    fused = reciprocal_rank_fusion(
        {"vector": vector_hits, "lexical": lexical_hits},
        weights={"vector": 1.0, "lexical": 1.0},
    )
    assert len(fused) == 1
    assert fused[0].record_id == record.record_id


def test_score_ties_break_by_record_id() -> None:
    left = _record("b-record", "alpha beta")
    right = _record("a-record", "alpha beta")
    hits_a = (
        VectorSearchResult(record_id=left.record_id, score=1.0, record=left),
        VectorSearchResult(record_id=right.record_id, score=1.0, record=right),
    )
    hits_b = (
        VectorSearchResult(record_id=right.record_id, score=1.0, record=right),
        VectorSearchResult(record_id=left.record_id, score=1.0, record=left),
    )
    fused = reciprocal_rank_fusion(
        {"vector": hits_a, "lexical": hits_b},
        weights={"vector": 1.0, "lexical": 1.0},
    )
    # Equal RRF contributions → stable record_id ascending.
    assert [item.record_id for item in fused] == sorted(
        item.record_id for item in fused
    )


def test_repository_isolation_lexical() -> None:
    store = InMemoryVectorStore()
    store.upsert(
        [
            _record("in", "owners controller", repository_id="repo-a"),
            _record("out", "owners controller", repository_id="repo-b"),
        ]
    )
    retriever = _retriever(store, mode="lexical")
    result = retriever.retrieve(
        RetrievalRequest(query="owners controller", scope=_scope(repository_id="repo-a"))
    )
    assert result.context is not None
    assert all(h.repository_id == "repo-a" for h in result.context.hits)


def test_incompatible_vector_index_fails_clearly() -> None:
    store = InMemoryVectorStore()
    record = _record("x", "owners controller")
    # Stamp as openai so deterministic query fails compatibility.
    meta = dict(record.metadata)
    meta["embedding_provider"] = "openai"
    meta["embedding_config_fingerprint"] = "other"
    stamped = VectorRecord(
        record_id=record.record_id,
        namespace=record.namespace,
        entity_id=record.entity_id,
        embedding=record.embedding,
        metadata=meta,
        text=record.text,
        fingerprint=record.fingerprint,
    )
    store.upsert([stamped])
    retriever = _retriever(store, mode="vector")
    result = retriever.retrieve(
        RetrievalRequest(query="owners controller", scope=_scope())
    )
    assert result.status == RetrievalStatus.FAILED
    assert any(d.code == "embedding_index_incompatible" for d in result.diagnostics)


def test_lexical_search_ranks_relevant_text() -> None:
    records = [
        _record("noise", "completely unrelated packaging metadata"),
        _record("hit", "OwnersController manages petclinic owners"),
    ]
    hits = lexical_search("OwnersController owners", records, top_k=2)
    assert hits
    assert hits[0].record_id == records[1].record_id


def test_settings_mode_validation() -> None:
    with pytest.raises(ValueError, match="mode"):
        KnowledgeRetrievalSettings(mode="rerank")
    settings = KnowledgeRetrievalSettings(result_limit=7)
    assert settings.resolve_result_limit() == 7
    assert KnowledgeRetrievalSettings().resolve_result_limit() == 10


def test_hybrid_grounded_answer_citations_unchanged() -> None:
    from codestrata.config.settings import KnowledgeAnsweringSettings
    from codestrata_platform.rag.application.answering import (
        DeterministicExtractiveAnswerProvider,
        GroundedAnswerEngine,
    )
    from codestrata_platform.rag.domain.answering import GroundedAnswerRequest

    store = InMemoryVectorStore()
    store.upsert([_record("owners", "OwnersController handles pet clinic owners.")])
    retriever = _retriever(store, mode="hybrid")
    engine = GroundedAnswerEngine(
        retriever=retriever,
        answer_provider=DeterministicExtractiveAnswerProvider(),
        answering_settings=KnowledgeAnsweringSettings(enabled=True),
        retrieval_settings=KnowledgeRetrievalSettings(enabled=True, mode="hybrid"),
    )
    result = engine.answer(
        GroundedAnswerRequest(
            question="What handles owners?",
            scope=_scope(),
            top_k=5,
        )
    )
    assert result.answer is not None
    assert result.answer.citations
    assert all(c.citation_label.startswith("SRC-") for c in result.answer.citations)
