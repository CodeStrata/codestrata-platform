"""Dogfood: MCP repository-intelligence tools via FastMCP call_tool (Phase 5.7).

TEST/DOGFOOD — repository_answer uses deterministic extractive answering,
not production generative AI.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from codestrata.application.assessment import AssessmentApplicationService
from codestrata.application.knowledge.queries import KnowledgeQueryService
from codestrata.config import CodestrataSettings
from codestrata.config.settings import (
    KnowledgeAnsweringSettings,
    KnowledgeEmbeddingSettings,
    KnowledgeRetrievalSettings,
)
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
from codestrata_platform.rag.vector_store import InMemoryVectorStore

QUESTIONS = [
    "How is the repository architecture organized?",
    "What are the highest-severity security findings?",
    "Which dependencies create modernization risk?",
    "Where is authentication implemented?",
    "What testing limitations were identified?",
    "What performance risks exist?",
    "How is cloud configuration handled?",
    "What technical-debt recommendations were generated?",
]

CORPORA: dict[str, list[tuple[str, str, dict[str, object]]]] = {
    "codestrata": [
        (
            "arch",
            "The CodeStrata architecture is organized as layered packages.",
            {"source_type": "architecture", "file_path": "ARCHITECTURE.md"},
        ),
        (
            "sec",
            "A high severity security finding notes secret redaction gaps.",
            {"source_type": "security", "severity": "high", "finding_id": "sec-1"},
        ),
        (
            "dep",
            "Dependency modernization risk includes outdated transitive packages.",
            {"source_type": "dependency"},
        ),
    ],
    "spring-petclinic": [
        (
            "arch",
            "Spring Petclinic architecture is organized around owners pets and vets.",
            {"source_type": "architecture"},
        ),
        (
            "sec",
            "Security findings highlight default in-memory credentials.",
            {"source_type": "security", "severity": "medium"},
        ),
    ],
    "synthetic-multilang": [
        (
            "arch",
            "Synthetic multi-language architecture mixes Python and TypeScript packages.",
            {"source_type": "architecture"},
        ),
        (
            "perf",
            "Performance risks exist in synchronous bundle builds.",
            {"source_type": "performance"},
        ),
    ],
}

TOOLS = [
    "repository_health",
    "repository_search",
    "repository_answer",
    "repository_findings",
    "repository_recommendations",
    "repository_assessments",
    "repository_architecture",
    "repository_security",
    "repository_dependencies",
    "repository_tests",
    "repository_cloud",
    "repository_ai_readiness",
    "repository_performance",
]


def _settings(knowledge_dir: Path) -> CodestrataSettings:
    return CodestrataSettings.model_validate(
        {
            "repository": {"path": "."},
            "workspace": {"directory": ".codestrata-workspace"},
            "knowledge": {
                "directory": str(knowledge_dir),
                "retrieval": {"enabled": True},
                "answering": {
                    "enabled": True,
                    "provider": "deterministic_extractive",
                },
                "embedding": {
                    "enabled": True,
                    "provider": "deterministic",
                    "dimension": 32,
                },
                "vector_store": {"provider": "memory"},
            },
            "static_analysis": {"enabled": False},
            "ai": {"bedrock": {}},
            "mcp": {"enabled": True, "transport": "stdio", "log_level": "WARNING"},
        }
    )


def _index(corpus: str, dimension: int = 32) -> InMemoryVectorStore:
    provider = DeterministicEmbeddingProvider(dimension=dimension)
    store = InMemoryVectorStore()
    records = []
    for entity_id, text, extra in CORPORA[corpus]:
        records.append(
            VectorRecord.create(
                entity_id=f"{corpus}-{entity_id}",
                embedding=list(provider.embed_text(text).embedding),
                text=text,
                metadata={
                    "tenant_id": "dogfood",
                    "repository_id": corpus,
                    "scan_id": "scan-dogfood",
                    "document_id": f"kd:{corpus}:{entity_id}",
                    "chunk_id": f"kc:{corpus}:{entity_id}",
                    "chunk_sequence": 0,
                    "content_hash": f"hash-{corpus}-{entity_id}",
                    **extra,
                },
            )
        )
    store.upsert(records)
    return store


async def _call(server: Any, name: str, arguments: dict[str, Any] | None = None) -> Any:
    result = await server.call_tool(name, arguments or {})
    if isinstance(result, tuple):
        structured = result[1]
        if isinstance(structured, dict) and set(structured.keys()) == {"result"}:
            return structured["result"]
        return structured
    return result


def _size(payload: Any) -> int:
    return len(dumps_stable_json(payload))


async def dogfood_corpus(corpus: str, root: Path) -> dict[str, Any]:
    knowledge_dir = root / "knowledge" / corpus
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    with SqliteKnowledgeStore(knowledge_dir) as store:
        settings = _settings(knowledge_dir)
        queries = KnowledgeQueryService(store)
        vector = _index(corpus)
        provider = DeterministicEmbeddingProvider(dimension=32)
        retriever = RepositoryRetriever(
            embedding_provider=provider,
            vector_store=vector,
            retrieval_settings=KnowledgeRetrievalSettings(enabled=True),
            embedding_settings=KnowledgeEmbeddingSettings(
                enabled=True, provider="deterministic", dimension=32
            ),
        )
        answer_provider = DeterministicExtractiveAnswerProvider()
        engine = GroundedAnswerEngine(
            retriever=retriever,
            answer_provider=answer_provider,
            answering_settings=KnowledgeAnsweringSettings(enabled=True),
            retrieval_settings=KnowledgeRetrievalSettings(enabled=True),
        )
        context = RepositoryIntelligenceContext(
            queries=queries,
            settings=settings,
            mcp=settings.mcp,
            retriever=retriever,
            answer_engine=engine,
            answer_provider=answer_provider,
            embedding_provider=provider,
            vector_store=vector,
            vector_store_provider="memory",
            vector_store_persistent=False,
        )
        server = create_mcp_server(
            query_service=queries,
            assessment_service=AssessmentApplicationService(),
            settings=settings,
            repository_intelligence=context,
        )
        tools = sorted(tool.name for tool in await server.list_tools())
        rows: list[dict[str, Any]] = []
        for tool in TOOLS:
            if tool == "repository_health":
                first = await _call(server, tool, {})
                second = await _call(server, tool, {})
                rows.append(
                    {
                        "tool": tool,
                        "status": first.get("status"),
                        "result_count": None,
                        "response_size": _size(first),
                        "determinism": first.get("fingerprint")
                        == second.get("fingerprint"),
                        "provider_mode": "memory+deterministic_extractive",
                        "transport": "stdio",
                    }
                )
                continue
            if tool in {"repository_search", "repository_answer"}:
                for question in QUESTIONS[:3]:
                    args = {
                        "tenant_id": "dogfood",
                        "repository_id": corpus,
                        ("query" if tool == "repository_search" else "question"): question,
                    }
                    first = await _call(server, tool, args)
                    second = await _call(server, tool, args)
                    data = first.get("data") or {}
                    citations = len(
                        data.get("citations") or data.get("citation_labels") or []
                    )
                    rows.append(
                        {
                            "tool": tool,
                            "question": question,
                            "status": first.get("status"),
                            "result_count": (first.get("coverage") or {}).get(
                                "result_count"
                            ),
                            "citations": citations,
                            "response_size": _size(first),
                            "determinism": first.get("fingerprint")
                            == second.get("fingerprint"),
                            "provider_mode": "memory+deterministic_extractive",
                            "transport": "stdio",
                            "generative": False,
                        }
                    )
                continue
            args = {"tenant_id": "dogfood", "repository_id": corpus}
            first = await _call(server, tool, args)
            second = await _call(server, tool, args)
            data = first.get("data") or {}
            rows.append(
                {
                    "tool": tool,
                    "status": first.get("status"),
                    "result_count": (first.get("coverage") or {}).get("result_count"),
                    "findings": len(data.get("findings") or []),
                    "recommendations": len(data.get("recommendations") or []),
                    "response_size": _size(first),
                    "determinism": first.get("fingerprint")
                    == second.get("fingerprint"),
                    "provider_mode": "memory+deterministic_extractive",
                    "transport": "stdio",
                }
            )
        return {
            "corpus": corpus,
            "label": "TEST/DOGFOOD — deterministic extractive answers (not production AI)",
            "tools_listed": tools,
            "calls": rows,
        }


def main() -> None:
    root = Path(__file__).resolve().parents[4] / "reports" / "mcp-dogfood"
    root.mkdir(parents=True, exist_ok=True)
    report = {"corpora": {}}
    for corpus in CORPORA:
        result = asyncio.run(dogfood_corpus(corpus, root))
        report["corpora"][corpus] = result  # type: ignore[index]
        (root / f"{corpus}-mcp.json").write_text(
            dumps_stable_json(result), encoding="utf-8"
        )
        print(f"=== {corpus} === tools={len(result['tools_listed'])} calls={len(result['calls'])}")
        for row in result["calls"]:
            print(
                f"- {row['tool']:28} status={row.get('status')} "
                f"det={row.get('determinism')} size={row.get('response_size')}"
            )
    (root / "summary.json").write_text(dumps_stable_json(report), encoding="utf-8")
    print(json.dumps({"wrote": str(root)}, indent=2))


def test_mcp_dogfood_smoke(tmp_path: Path) -> None:
    result = asyncio.run(dogfood_corpus("codestrata", tmp_path))
    assert "repository_search" in result["tools_listed"]
    assert result["calls"]
    assert all(row.get("determinism") for row in result["calls"] if "determinism" in row)


if __name__ == "__main__":
    main()
