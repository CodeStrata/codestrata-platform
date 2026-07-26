#!/usr/bin/env python3
"""Dogfood Phase 5.9 hybrid retrieval on synthetic corpora.

Compares vector vs lexical vs hybrid for a fixed question set over in-memory
indexed snippets that approximate CodeStrata, Spring Petclinic, and
synthetic-multilang evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

from codestrata.config.settings import KnowledgeEmbeddingSettings, KnowledgeRetrievalSettings
from codestrata_platform.rag.application.retrieval import RepositoryRetriever
from codestrata_platform.rag.domain import RetrievalRequest, RetrievalScope
from codestrata_platform.rag.domain.vector import VectorRecord
from codestrata_platform.rag.embedding import DeterministicEmbeddingProvider
from codestrata_platform.rag.vector_store import InMemoryVectorStore

CORPORA: dict[str, list[tuple[str, str]]] = {
    "codestrata": [
        ("arch", "CodeStrata repository knowledge layer projects assessment graphs."),
        ("mcp", "MCP repository_search exposes retrieval over indexed chunks."),
        ("rules", "Rule engine evaluates architecture and dependency packs."),
    ],
    "spring-petclinic": [
        ("owners", "OwnersController handles CRUD for petclinic owners."),
        ("visits", "Visit entity stores clinic appointment details."),
        ("pom", "Maven pom.xml declares spring-boot-starter-data-jpa."),
    ],
    "synthetic-multilang": [
        ("py", "Python FastAPI service exposes /health endpoint."),
        ("js", "JavaScript package.json lists express as a dependency."),
        ("java", "Java Spring Boot Application main class bootstraps the app."),
    ],
}

QUESTIONS = (
    "OwnersController petclinic owners",
    "repository knowledge MCP search",
    "FastAPI health endpoint",
)


def _scope(repo: str) -> RetrievalScope:
    return RetrievalScope(tenant_id="dogfood", repository_id=repo)


def _index(corpus: str) -> InMemoryVectorStore:
    store = InMemoryVectorStore()
    provider = DeterministicEmbeddingProvider(dimension=32)
    records: list[VectorRecord] = []
    for entity_id, text in CORPORA[corpus]:
        records.append(
            VectorRecord.create(
                entity_id=f"{corpus}:{entity_id}",
                embedding=list(provider.embed_text(text).embedding),
                metadata={
                    "tenant_id": "dogfood",
                    "repository_id": corpus,
                    "scan_id": "scan-dogfood",
                    "document_id": f"kd:{corpus}:{entity_id}",
                    "chunk_id": f"kc:{corpus}:{entity_id}",
                    "chunk_sequence": 0,
                    "content_hash": f"hash-{corpus}-{entity_id}",
                    "embedding_provider": "deterministic",
                    "embedding_model": "deterministic-test-embedding",
                    "embedding_model_version": "1.0.0",
                    "embedding_dimension": 32,
                },
                text=text,
            )
        )
    store.upsert(records)
    return store


def _run(mode: str, store: InMemoryVectorStore, repo: str, question: str) -> dict[str, object]:
    retriever = RepositoryRetriever(
        embedding_provider=DeterministicEmbeddingProvider(dimension=32),
        vector_store=store,
        retrieval_settings=KnowledgeRetrievalSettings(
            enabled=True,
            mode=mode,
            top_k=3,
            candidate_limit=10,
        ),
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True,
            provider="deterministic",
            dimension=32,
        ),
    )
    result = retriever.retrieve(RetrievalRequest(query=question, scope=_scope(repo), top_k=3))
    hits = []
    if result.context is not None:
        hits = [
            {
                "rank": hit.rank,
                "score": hit.score,
                "record_id": hit.record_id,
                "excerpt": (hit.content or "")[:120],
            }
            for hit in result.context.hits
        ]
    return {
        "mode": mode,
        "status": result.status.value,
        "hits": hits,
        "coverage": result.coverage.model_dump(mode="json") if result.coverage else {},
    }


def main() -> None:
    report: dict[str, object] = {"questions": list(QUESTIONS), "corpora": {}}
    for corpus in CORPORA:
        store = _index(corpus)
        corpus_report: dict[str, object] = {}
        for question in QUESTIONS:
            corpus_report[question] = {
                mode: _run(mode, store, corpus, question)
                for mode in ("vector", "lexical", "hybrid")
            }
        report["corpora"][corpus] = corpus_report

    out = Path("reports/hybrid-retrieval-dogfood")
    out.mkdir(parents=True, exist_ok=True)
    path = out / "comparison.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {path}")
    # Brief console comparison for the petclinic owners question.
    pet = report["corpora"]["spring-petclinic"]["OwnersController petclinic owners"]
    for mode, payload in pet.items():  # type: ignore[union-attr]
        top = (payload.get("hits") or [{}])[0]
        print(f"{mode:8} top={top.get('record_id')} score={top.get('score')}")


if __name__ == "__main__":
    main()
