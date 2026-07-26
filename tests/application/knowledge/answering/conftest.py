"""Helpers and fixtures for Phase 5.6 grounded answering tests."""

from __future__ import annotations

from aimf.application.knowledge.answering import (
    DeterministicExtractiveAnswerProvider,
    GroundedAnswerEngine,
)
from aimf.application.knowledge.retrieval import RepositoryRetriever
from aimf.config.settings import (
    KnowledgeAnsweringSettings,
    KnowledgeEmbeddingSettings,
    KnowledgeRetrievalSettings,
)
from aimf.domain.knowledge import (
    RetrievalScope,
    VectorRecord,
)
from aimf.infrastructure.embedding import DeterministicEmbeddingProvider
from aimf.infrastructure.vector_store import InMemoryVectorStore


def scope(**kwargs: str) -> RetrievalScope:
    base = {"tenant_id": "tenant-a", "repository_id": "repo-a"}
    base.update(kwargs)
    return RetrievalScope(**base)  # type: ignore[arg-type]


def record(
    entity_id: str,
    text: str,
    *,
    embedding: list[float] | None = None,
    tenant_id: str = "tenant-a",
    repository_id: str = "repo-a",
    scan_id: str = "scan-a",
    document_id: str | None = None,
    chunk_id: str | None = None,
    sequence: int = 0,
    dimension: int = 8,
    **extra: object,
) -> VectorRecord:
    meta: dict[str, object] = {
        "tenant_id": tenant_id,
        "repository_id": repository_id,
        "scan_id": scan_id,
        "document_id": document_id or f"kd:{entity_id}",
        "chunk_id": chunk_id or f"kc:{entity_id}",
        "chunk_sequence": sequence,
        "content_hash": f"hash-{entity_id}",
        **extra,
    }
    provider = DeterministicEmbeddingProvider(dimension=dimension)
    vector = embedding or list(provider.embed_text(text).embedding)
    return VectorRecord.create(
        entity_id=entity_id,
        embedding=vector,
        metadata=meta,
        text=text,
    )


def build_engine(
    *,
    store: InMemoryVectorStore | None = None,
    answering_enabled: bool = True,
    retrieval_enabled: bool = True,
    dimension: int = 8,
    answering: KnowledgeAnsweringSettings | None = None,
) -> tuple[GroundedAnswerEngine, InMemoryVectorStore, DeterministicEmbeddingProvider]:
    vector_store = store or InMemoryVectorStore()
    provider = DeterministicEmbeddingProvider(dimension=dimension)
    retriever = RepositoryRetriever(
        embedding_provider=provider,
        vector_store=vector_store,
        retrieval_settings=KnowledgeRetrievalSettings(enabled=retrieval_enabled),
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True,
            provider="deterministic",
            dimension=dimension,
        ),
    )
    answer_provider = DeterministicExtractiveAnswerProvider()
    engine = GroundedAnswerEngine(
        retriever=retriever,
        answer_provider=answer_provider,
        answering_settings=answering
        or KnowledgeAnsweringSettings(enabled=answering_enabled),
        retrieval_settings=KnowledgeRetrievalSettings(enabled=retrieval_enabled),
    )
    return engine, vector_store, provider
