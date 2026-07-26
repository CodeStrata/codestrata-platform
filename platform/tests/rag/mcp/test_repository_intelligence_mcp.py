"""Phase 5.7 repository-intelligence MCP tool tests."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from codestrata.application.assessment import AssessmentApplicationService
from codestrata.application.knowledge.queries import KnowledgeQueryService
from codestrata.config import (
    CodestrataSettings,
    KnowledgeAnsweringSettings,
    KnowledgeRetrievalSettings,
)
from codestrata.config.settings import KnowledgeEmbeddingSettings, McpSettings, McpToolsSettings
from codestrata.infrastructure.knowledge_store import SqliteKnowledgeStore
from codestrata.interfaces.mcp import create_mcp_server
from codestrata.interfaces.mcp.context import RepositoryIntelligenceContext
from codestrata.services.artifact_serialization import dumps_stable_json
from codestrata_platform.rag.application.answering import (
    DeterministicExtractiveAnswerProvider,
    GroundedAnswerEngine,
)
from codestrata_platform.rag.application.retrieval import RepositoryRetriever
from codestrata_platform.rag.domain import VectorRecord
from codestrata_platform.rag.embedding import DeterministicEmbeddingProvider
from codestrata_platform.rag.mcp.composition import compose_repository_intelligence
from codestrata_platform.rag.mcp.registry import (
    TOOL_NAME_ALIASES,
    RepositoryIntelligenceToolRegistry,
    ToolRegistryError,
)
from codestrata_platform.rag.vector_store import InMemoryVectorStore


def _settings(
    *,
    knowledge_dir: Path,
    retrieval: bool = True,
    answering: bool = True,
    mcp_enabled: bool = True,
    tools: dict[str, bool] | None = None,
) -> CodestrataSettings:
    tool_cfg = McpToolsSettings()
    if tools:
        tool_cfg = McpToolsSettings.model_validate(tools)
    return CodestrataSettings.model_validate(
        {
            "repository": {"path": "."},
            "workspace": {"directory": ".codestrata-workspace"},
            "knowledge": {
                "directory": str(knowledge_dir),
                "retrieval": {"enabled": retrieval},
                "answering": {
                    "enabled": answering,
                    "provider": "deterministic_extractive",
                },
                "embedding": {
                    "enabled": True,
                    "provider": "deterministic",
                    "dimension": 8,
                },
                "vector_store": {"provider": "memory"},
            },
            "static_analysis": {"enabled": False},
            "ai": {"bedrock": {}},
            "mcp": {
                "enabled": mcp_enabled,
                "transport": "stdio",
                "log_level": "WARNING",
                "server_name": "codestrata",
                "tools": tool_cfg.model_dump(),
            },
        }
    )


def _record(entity_id: str, text: str, **extra: object) -> VectorRecord:
    provider = DeterministicEmbeddingProvider(dimension=8)
    return VectorRecord.create(
        entity_id=entity_id,
        embedding=list(provider.embed_text(text).embedding),
        text=text,
        metadata={
            "tenant_id": "tenant-a",
            "repository_id": "repo-a",
            "scan_id": "scan-a",
            "document_id": f"kd:{entity_id}",
            "chunk_id": f"kc:{entity_id}",
            "chunk_sequence": 0,
            "content_hash": f"hash-{entity_id}",
            **extra,
        },
    )


def _ri_context(
    queries: KnowledgeQueryService,
    settings: CodestrataSettings,
    store: InMemoryVectorStore,
    *,
    retrieval_mode: str = "vector",
) -> RepositoryIntelligenceContext:
    provider = DeterministicEmbeddingProvider(dimension=8)
    retrieval_settings = KnowledgeRetrievalSettings(
        enabled=True,
        mode=retrieval_mode,
    )
    retriever = RepositoryRetriever(
        embedding_provider=provider,
        vector_store=store,
        retrieval_settings=retrieval_settings,
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True, provider="deterministic", dimension=8
        ),
    )
    answer_provider = DeterministicExtractiveAnswerProvider()
    engine = GroundedAnswerEngine(
        retriever=retriever,
        answer_provider=answer_provider,
        answering_settings=KnowledgeAnsweringSettings(enabled=True),
        retrieval_settings=retrieval_settings,
    )
    return RepositoryIntelligenceContext(
        queries=queries,
        settings=settings,
        mcp=settings.mcp,
        retriever=retriever,
        answer_engine=engine,
        answer_provider=answer_provider,
        embedding_provider=provider,
        vector_store=store,
        vector_store_provider="memory",
        vector_store_persistent=False,
    )


async def _call(server: Any, name: str, arguments: dict[str, Any] | None = None) -> Any:
    result = await server.call_tool(name, arguments or {})
    if isinstance(result, tuple):
        structured = result[1]
        if isinstance(structured, dict) and set(structured.keys()) == {"result"}:
            return structured["result"]
        return structured
    if isinstance(result, list) and result:
        return json.loads(result[0].text)
    return result


def test_tool_aliases_documented() -> None:
    assert TOOL_NAME_ALIASES["repository.search"] == "repository_search"
    assert TOOL_NAME_ALIASES["repository.answer"] == "repository_answer"
    assert TOOL_NAME_ALIASES["repository.health"] == "repository_health"


def test_duplicate_tool_registration_rejected() -> None:
    registry = RepositoryIntelligenceToolRegistry()
    assert registry.register("repository_health") is True
    with pytest.raises(ToolRegistryError, match="duplicate"):
        registry.register("repository_health")


def test_disabled_tool_excluded(tmp_path: Path) -> None:
    with SqliteKnowledgeStore(tmp_path / "knowledge") as store:
        settings = _settings(
            knowledge_dir=tmp_path / "k",
            tools={"repository_answer": False},
        )
        queries = KnowledgeQueryService(store)
        server = create_mcp_server(
            query_service=queries,
            assessment_service=AssessmentApplicationService(),
            settings=settings,
            repository_intelligence=_ri_context(
                queries, settings, InMemoryVectorStore()
            ),
        )

        async def _check() -> None:
            names = {tool.name for tool in await server.list_tools()}
            assert "repository_search" in names
            assert "repository_answer" not in names
            assert "repository_health" in names

        asyncio.run(_check())


def test_repository_search_and_answer_determinism(tmp_path: Path) -> None:
    with SqliteKnowledgeStore(tmp_path / "knowledge") as store:
        settings = _settings(knowledge_dir=tmp_path / "k")
        queries = KnowledgeQueryService(store)
        vector = InMemoryVectorStore()
        vector.upsert(
            [
                _record(
                    "arch",
                    "The repository architecture is organized as layered packages.",
                    source_type="architecture",
                    file_path="ARCHITECTURE.md",
                )
            ]
        )
        server = create_mcp_server(
            query_service=queries,
            assessment_service=AssessmentApplicationService(),
            settings=settings,
            repository_intelligence=_ri_context(queries, settings, vector),
        )

        async def _run() -> None:
            args = {
                "query": "repository architecture organized",
                "tenant_id": "tenant-a",
                "repository_id": "repo-a",
                "top_k": 5,
            }
            first = await _call(server, "repository_search", args)
            second = await _call(server, "repository_search", args)
            assert first["status"] in {"success", "partial"}
            assert first["fingerprint"] == second["fingerprint"]
            assert dumps_stable_json(first) == dumps_stable_json(second)
            assert "embedding" not in dumps_stable_json(first).lower() or (
                '"embedding"' not in dumps_stable_json(first)
            )

            answer_args = {
                "question": "How is the repository architecture organized?",
                "tenant_id": "tenant-a",
                "repository_id": "repo-a",
            }
            a1 = await _call(server, "repository_answer", answer_args)
            a2 = await _call(server, "repository_answer", answer_args)
            assert a1["status"] in {
                "success",
                "partial",
                "insufficient_evidence",
                "empty",
            }
            assert a1["data"]["provider_notes"]["is_generative_ai"] is False
            assert a1["data"]["provider_notes"]["is_production_model"] is False
            assert a1["fingerprint"] == a2["fingerprint"]

        asyncio.run(_run())


def test_repository_search_requires_scope(tmp_path: Path) -> None:
    with SqliteKnowledgeStore(tmp_path / "knowledge") as store:
        settings = _settings(knowledge_dir=tmp_path / "k")
        queries = KnowledgeQueryService(store)
        server = create_mcp_server(
            query_service=queries,
            assessment_service=AssessmentApplicationService(),
            settings=settings,
            repository_intelligence=_ri_context(
                queries, settings, InMemoryVectorStore()
            ),
        )

        async def _run() -> None:
            with pytest.raises(ToolError):
                await _call(
                    server,
                    "repository_search",
                    {"query": "architecture", "tenant_id": "", "repository_id": "repo-a"},
                )

        asyncio.run(_run())


def test_retrieval_disabled_returns_disabled(tmp_path: Path) -> None:
    with SqliteKnowledgeStore(tmp_path / "knowledge") as store:
        settings = _settings(knowledge_dir=tmp_path / "k", retrieval=False)
        queries = KnowledgeQueryService(store)
        server = create_mcp_server(
            query_service=queries,
            assessment_service=AssessmentApplicationService(),
            settings=settings,
            repository_intelligence=_ri_context(
                queries, settings, InMemoryVectorStore()
            ),
        )

        async def _run() -> None:
            result = await _call(
                server,
                "repository_search",
                {
                    "query": "architecture",
                    "tenant_id": "tenant-a",
                    "repository_id": "repo-a",
                },
            )
            assert result["status"] == "disabled"
            assert any(
                d["code"] == "retrieval_disabled" for d in result["diagnostics"]
            )

        asyncio.run(_run())


def test_answering_disabled_returns_disabled(tmp_path: Path) -> None:
    with SqliteKnowledgeStore(tmp_path / "knowledge") as store:
        settings = _settings(knowledge_dir=tmp_path / "k", answering=False)
        queries = KnowledgeQueryService(store)
        server = create_mcp_server(
            query_service=queries,
            assessment_service=AssessmentApplicationService(),
            settings=settings,
            repository_intelligence=_ri_context(
                queries, settings, InMemoryVectorStore()
            ),
        )

        async def _run() -> None:
            result = await _call(
                server,
                "repository_answer",
                {
                    "question": "architecture?",
                    "tenant_id": "tenant-a",
                    "repository_id": "repo-a",
                },
            )
            assert result["status"] == "disabled"
            assert any(d["code"] == "answering_disabled" for d in result["diagnostics"])

        asyncio.run(_run())


def test_repository_health_no_secrets(tmp_path: Path) -> None:
    with SqliteKnowledgeStore(tmp_path / "knowledge") as store:
        settings = _settings(knowledge_dir=tmp_path / "k")
        queries = KnowledgeQueryService(store)
        server = create_mcp_server(
            query_service=queries,
            assessment_service=AssessmentApplicationService(),
            settings=settings,
            repository_intelligence=_ri_context(
                queries, settings, InMemoryVectorStore()
            ),
        )

        async def _run() -> None:
            result = await _call(server, "repository_health", {})
            text = dumps_stable_json(result)
            assert "postgresql://" not in text
            assert "password" not in text.lower()
            assert result["vector_store_provider"] == "memory"
            assert result["vector_store_persistent"] is False
            assert result.get("execution_profile") == settings.profile
            assert "embedding" not in text or '"embeddings"' not in text

        asyncio.run(_run())


def test_findings_and_assessments_empty_without_runs(tmp_path: Path) -> None:
    with SqliteKnowledgeStore(tmp_path / "knowledge") as store:
        settings = _settings(knowledge_dir=tmp_path / "k")
        queries = KnowledgeQueryService(store)
        server = create_mcp_server(
            query_service=queries,
            assessment_service=AssessmentApplicationService(),
            settings=settings,
            repository_intelligence=_ri_context(
                queries, settings, InMemoryVectorStore()
            ),
        )

        async def _run() -> None:
            findings = await _call(
                server,
                "repository_findings",
                {"tenant_id": "tenant-a", "repository_id": "missing-repo"},
            )
            assert findings["status"] == "empty"
            assessments = await _call(
                server,
                "repository_assessments",
                {"tenant_id": "tenant-a", "repository_id": "missing-repo"},
            )
            assert assessments["status"] == "empty"
            architecture = await _call(
                server,
                "repository_architecture",
                {"tenant_id": "tenant-a", "repository_id": "missing-repo"},
            )
            assert architecture["status"] == "empty"

        asyncio.run(_run())


def test_compose_memory_provider(tmp_path: Path) -> None:
    with SqliteKnowledgeStore(tmp_path / "knowledge") as store:
        settings = _settings(knowledge_dir=tmp_path / "k")
        ctx = compose_repository_intelligence(
            queries=KnowledgeQueryService(store),
            settings=settings,
        )
        assert ctx.vector_store_provider == "memory"
        assert ctx.vector_store_persistent is False
        assert ctx.retriever is not None
        assert ctx.answer_engine is not None
        assert ctx.answer_provider is not None
        assert ctx.answer_provider.model_identity().is_generative_ai is False


def test_mcp_transport_settings_accept_http_alias() -> None:
    settings = McpSettings(transport="http")
    assert settings.transport == "streamable-http"
    with pytest.raises(ValueError):
        McpSettings(transport="grpc")


@pytest.mark.skipif(
    not (
        __import__("os").environ.get("CODESTRATA_DATABASE_URL", "").strip()
        or __import__("os").environ.get("CODESTRATA_PGVECTOR_URL", "").strip()
    ),
    reason="CODESTRATA_DATABASE_URL / CODESTRATA_PGVECTOR_URL not set",
)
def test_compose_pgvector_when_configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_VECTOR_STORE_PROVIDER", "pgvector")
    with SqliteKnowledgeStore(tmp_path / "knowledge") as store:
        settings = _settings(knowledge_dir=tmp_path / "k")
        settings = settings.model_copy(
            update={
                "knowledge": settings.knowledge.model_copy(
                    update={
                        "vector_store": settings.knowledge.vector_store.model_copy(
                            update={"provider": "pgvector"}
                        )
                    }
                )
            }
        )
        ctx = compose_repository_intelligence(
            queries=KnowledgeQueryService(store),
            settings=settings,
        )
        # Either healthy pgvector composition or sanitized diagnostic — never silent memory.
        if ctx.vector_store is not None:
            assert ctx.vector_store_provider == "pgvector"
            assert ctx.vector_store_persistent is True
        else:
            assert any(
                item.get("code") == "vector_store_unavailable"
                for item in ctx.composition_diagnostics
            )


def test_mcp_repository_search_uses_hybrid_mode(tmp_path: Path) -> None:
    with SqliteKnowledgeStore(tmp_path / "knowledge") as store:
        settings = _settings(knowledge_dir=tmp_path / "k")
        queries = KnowledgeQueryService(store)
        vector = InMemoryVectorStore()
        vector.upsert(
            [
                _record(
                    "owners",
                    "OwnersController handles petclinic owners.",
                    source_type="code",
                    file_path="OwnersController.java",
                )
            ]
        )
        server = create_mcp_server(
            query_service=queries,
            assessment_service=AssessmentApplicationService(),
            settings=settings,
            repository_intelligence=_ri_context(
                queries, settings, vector, retrieval_mode="hybrid"
            ),
        )

        async def _run() -> None:
            payload = await _call(
                server,
                "repository_search",
                {
                    "query": "OwnersController owners",
                    "tenant_id": "tenant-a",
                    "repository_id": "repo-a",
                    "top_k": 5,
                },
            )
            data = payload.get("data") or payload
            coverage = data.get("coverage") or {}
            assert coverage.get("retrieval_mode") == "hybrid"
            diagnostics = data.get("diagnostics") or []
            assert any(
                (d.get("code") == "retrieval_mode" and d.get("message") == "hybrid")
                or (
                    isinstance(d, dict)
                    and d.get("code") == "retrieval_stats"
                    and "mode=hybrid" in str(d.get("message", ""))
                )
                for d in diagnostics
            )
            answer = await _call(
                server,
                "repository_answer",
                {
                    "question": "What handles owners?",
                    "tenant_id": "tenant-a",
                    "repository_id": "repo-a",
                    "top_k": 5,
                },
            )
            answer_data = answer.get("data") or answer
            citations = (
                (answer_data.get("answer") or {}).get("citations")
                or answer_data.get("citations")
                or []
            )
            assert citations, "grounded answer must preserve citations"

        asyncio.run(_run())
