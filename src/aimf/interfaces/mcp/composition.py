"""Compose repository-intelligence dependencies for MCP (Phase 5.7)."""

from __future__ import annotations

from typing import Any

from aimf.application.knowledge.answering import (
    GroundedAnswerEngine,
    create_answer_provider,
)
from aimf.application.knowledge.answering.factory import AnswerProviderConfigurationError
from aimf.application.knowledge.queries import KnowledgeQueryService
from aimf.application.knowledge.retrieval import create_repository_retriever
from aimf.config import AimfSettings, McpSettings
from aimf.infrastructure.embedding import create_embedding_provider
from aimf.infrastructure.vector_store import create_vector_store
from aimf.infrastructure.vector_store.resolution import (
    resolve_vector_store_provider,
)
from aimf.interfaces.mcp.context import RepositoryIntelligenceContext
from aimf.security.database_url import sanitize_exception_message


def compose_repository_intelligence(
    *,
    queries: KnowledgeQueryService,
    settings: AimfSettings | None,
    mcp_settings: McpSettings | None = None,
    retriever: Any | None = None,
    answer_engine: Any | None = None,
    answer_provider: Any | None = None,
    embedding_provider: Any | None = None,
    vector_store: Any | None = None,
) -> RepositoryIntelligenceContext:
    """Build or accept injected repository-intelligence services.

    Never silently falls back from pgvector to memory. Composition failures are
    captured as sanitized diagnostics so Phase 2 MCP tools can still start.
    """

    mcp = mcp_settings or (settings.mcp if settings is not None else McpSettings())
    diagnostics: list[dict[str, Any]] = []
    knowledge = settings.knowledge if settings is not None else None
    provider_name = "memory"
    persistent = False
    store = vector_store
    embedder = embedding_provider
    repo_retriever = retriever
    provider = answer_provider
    engine = answer_engine

    if knowledge is not None:
        try:
            provider_name = resolve_vector_store_provider(knowledge)
            persistent = provider_name == "pgvector"
        except Exception as exc:  # noqa: BLE001 - composition boundary
            diagnostics.append(
                {
                    "code": "vector_store_provider_resolution_failed",
                    "message": sanitize_exception_message(str(exc)),
                    "severity": "error",
                }
            )

    if store is None and knowledge is not None:
        try:
            store = create_vector_store(knowledge)
        except Exception as exc:  # noqa: BLE001
            diagnostics.append(
                {
                    "code": "vector_store_unavailable",
                    "message": sanitize_exception_message(str(exc)),
                    "severity": "error",
                }
            )

    if embedder is None and knowledge is not None:
        try:
            embedder = create_embedding_provider(
                knowledge.embedding,
                aimf_settings=settings,
            )
        except Exception as exc:  # noqa: BLE001
            diagnostics.append(
                {
                    "code": "embedding_provider_unavailable",
                    "message": sanitize_exception_message(str(exc)),
                    "severity": "error",
                }
            )

    if (
        repo_retriever is None
        and store is not None
        and embedder is not None
        and knowledge is not None
    ):
        try:
            repo_retriever = create_repository_retriever(
                retrieval_settings=knowledge.retrieval,
                embedding_settings=knowledge.embedding,
                vector_store=store,
                embedding_provider=embedder,
            )
        except Exception as exc:  # noqa: BLE001
            diagnostics.append(
                {
                    "code": "retriever_unavailable",
                    "message": sanitize_exception_message(str(exc)),
                    "severity": "error",
                }
            )

    if provider is None and knowledge is not None:
        try:
            provider = create_answer_provider(
                knowledge.answering,
                aimf_settings=settings,
            )
        except AnswerProviderConfigurationError as exc:
            diagnostics.append(
                {
                    "code": "answer_provider_unavailable",
                    "message": sanitize_exception_message(str(exc)),
                    "severity": "error",
                }
            )
        except Exception as exc:  # noqa: BLE001
            diagnostics.append(
                {
                    "code": "answer_provider_unavailable",
                    "message": sanitize_exception_message(str(exc)),
                    "severity": "error",
                }
            )

    if (
        engine is None
        and repo_retriever is not None
        and provider is not None
        and knowledge is not None
    ):
        engine = GroundedAnswerEngine(
            retriever=repo_retriever,
            answer_provider=provider,
            answering_settings=knowledge.answering,
            retrieval_settings=knowledge.retrieval,
        )

    return RepositoryIntelligenceContext(
        queries=queries,
        settings=settings,
        mcp=mcp,
        retriever=repo_retriever,
        answer_engine=engine,
        answer_provider=provider,
        embedding_provider=embedder,
        vector_store=store,
        vector_store_provider=provider_name,
        vector_store_persistent=persistent,
        composition_diagnostics=tuple(diagnostics),
    )
