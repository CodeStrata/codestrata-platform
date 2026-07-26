"""Post-onboard grounded Q&A and MCP health helpers for acceptance."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

from codestrata.application.acceptance.targets import PREDEFINED_QUESTIONS
from codestrata.application.knowledge.ports import KnowledgeStore
from codestrata.application.knowledge.queries import KnowledgeQueryService
from codestrata.config.settings import (
    CodestrataSettings,
    KnowledgeAnsweringSettings,
    KnowledgeEmbeddingSettings,
    KnowledgeRetrievalSettings,
)
from codestrata.infrastructure.knowledge_store import SqliteKnowledgeStore
from codestrata_platform.rag.application.answering import (
    DeterministicExtractiveAnswerProvider,
    GroundedAnswerEngine,
)
from codestrata_platform.rag.application.indexing import (
    KnowledgeIndexRequest,
    create_knowledge_indexer,
)
from codestrata_platform.rag.application.retrieval import RepositoryRetriever
from codestrata_platform.rag.domain import GroundedAnswerRequest, KnowledgeCorpus, RetrievalScope
from codestrata_platform.rag.domain.vector import IndexScope
from codestrata_platform.rag.embedding import DeterministicEmbeddingProvider
from codestrata_platform.rag.vector_store import InMemoryVectorStore


def load_corpus_from_run(run_directory: Path) -> KnowledgeCorpus | None:
    """Load ``repository-knowledge-corpus.json`` written during onboard."""

    path = run_directory / "repository-knowledge-corpus.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return KnowledgeCorpus.model_validate(payload)


def build_answer_stack(
    corpus: KnowledgeCorpus,
    *,
    repository_id: str,
    scan_id: str,
    settings: CodestrataSettings,
) -> tuple[
    GroundedAnswerEngine,
    RetrievalScope,
    InMemoryVectorStore,
    DeterministicExtractiveAnswerProvider,
]:
    """Index the onboarded corpus into memory and build a grounded answer engine."""

    dimension = int(settings.knowledge.embedding.dimension)
    store = InMemoryVectorStore()
    embedder = DeterministicEmbeddingProvider(dimension=dimension)
    answer_provider = DeterministicExtractiveAnswerProvider()
    indexer = create_knowledge_indexer(
        embedding_settings=settings.knowledge.embedding.model_copy(
            update={"enabled": True, "provider": "deterministic", "dimension": dimension}
        ),
        indexing_settings=settings.knowledge.indexing.model_copy(update={"enabled": True}),
        vector_store=store,
        embedding_provider=embedder,
    )
    indexer.index(
        KnowledgeIndexRequest(
            corpus=corpus,
            scope=IndexScope(
                tenant_id="acceptance",
                repository_id=repository_id,
                scan_id=scan_id,
            ),
            prior_manifest=None,
        )
    )
    retrieval = KnowledgeRetrievalSettings(enabled=True)
    answering = KnowledgeAnsweringSettings(
        enabled=True,
        provider="deterministic_extractive",
        fail_on_insufficient_evidence=False,
    )
    embedding = KnowledgeEmbeddingSettings(
        enabled=True, provider="deterministic", dimension=dimension
    )
    retriever = RepositoryRetriever(
        embedding_provider=embedder,
        vector_store=store,
        retrieval_settings=retrieval,
        embedding_settings=embedding,
    )
    engine = GroundedAnswerEngine(
        retriever=retriever,
        answer_provider=answer_provider,
        answering_settings=answering,
        retrieval_settings=retrieval,
    )
    scope = RetrievalScope(
        tenant_id="acceptance",
        repository_id=repository_id,
        scan_id=scan_id,
    )
    return engine, scope, store, answer_provider


def ask_predefined_questions(
    engine: GroundedAnswerEngine,
    scope: RetrievalScope,
) -> list[dict[str, Any]]:
    """Ask the predefined acceptance questions and return compact rows."""

    rows: list[dict[str, Any]] = []
    for question in PREDEFINED_QUESTIONS:
        result = engine.answer(
            GroundedAnswerRequest(
                question=question,
                scope=scope,
                top_k=5,
                fail_on_insufficient_evidence=False,
            )
        )
        answer = result.answer
        rows.append(
            {
                "question": question,
                "status": result.status.value,
                "statements": len(answer.statements) if answer else 0,
                "citations": len(answer.citations) if answer else 0,
            }
        )
    return rows


def questions_passed(rows: list[dict[str, Any]]) -> tuple[bool, str]:
    """Acceptance bar for grounded Q&A against a live corpus."""

    if not rows:
        return False, "no questions executed"
    hard_failures = [row for row in rows if row.get("status") in {"failed", "disabled"}]
    if hard_failures:
        return False, f"{len(hard_failures)} question(s) failed or disabled"
    grounded = [
        row
        for row in rows
        if row.get("status") in {"success", "partial"} and int(row.get("citations") or 0) > 0
    ]
    if not grounded:
        soft = [
            row
            for row in rows
            if row.get("status") in {"success", "partial", "insufficient_evidence", "empty"}
        ]
        if len(soft) == len(rows):
            return True, "pipeline ok (limited topical coverage)"
        return False, "no grounded answers produced"
    return True, f"{len(grounded)}/{len(rows)} grounded answers with citations"


def mcp_health_check(
    settings: CodestrataSettings,
    *,
    vector_store: InMemoryVectorStore | None = None,
    answer_engine: GroundedAnswerEngine | None = None,
    answer_provider: DeterministicExtractiveAnswerProvider | None = None,
) -> dict[str, Any]:
    """Compose MCP server and invoke repository_health (no long-lived transport)."""

    try:
        from codestrata.interfaces.mcp import create_mcp_server
    except ImportError as error:  # pragma: no cover - optional extra
        raise RuntimeError(
            "MCP health requires the optional mcp extra.\n"
            "Fix: pip install 'codestrata[mcp]'"
        ) from error

    knowledge_dir = Path(settings.knowledge.directory) / "mcp-store"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    store = cast(KnowledgeStore, SqliteKnowledgeStore(knowledge_dir))
    queries = KnowledgeQueryService(store)
    server = create_mcp_server(
        settings=settings,
        query_service=queries,
        knowledge_store=store,
        vector_store=vector_store,
        answer_engine=answer_engine,
        answer_provider=answer_provider,
    )

    async def _health() -> Any:
        return await server.call_tool("repository_health", {})

    raw = asyncio.run(_health())
    return _normalize_tool_payload(raw)


def mcp_health_passed(payload: dict[str, Any]) -> tuple[bool, str]:
    """Interpret MCP health payload for acceptance."""

    status = str(payload.get("status") or payload.get("overall_status") or "").lower()
    if status in {"failed", "error", "unhealthy"}:
        return False, status
    nested = payload.get("result")
    if isinstance(nested, dict):
        return mcp_health_passed(nested)
    if status in {"success", "partial", "ok", "healthy", "pass", "passed"}:
        return True, status
    if payload.get("healthy") is False:
        return False, "unhealthy"
    if payload:
        return True, status or "composed"
    return False, "empty health payload"


def _normalize_tool_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, tuple) and len(raw) >= 2 and isinstance(raw[1], dict):
        return raw[1]
    structured = getattr(raw, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    data = getattr(raw, "data", None)
    if isinstance(data, dict):
        return data
    content = getattr(raw, "content", None)
    if isinstance(content, list) and content:
        first = content[0]
        body = getattr(first, "text", None)
        if isinstance(body, str):
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return {"raw": body}
    return {"raw": str(raw)}
