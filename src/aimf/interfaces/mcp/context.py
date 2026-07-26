"""Injected repository-intelligence services for MCP tools (Phase 5.7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aimf.application.knowledge.answering.engine import GroundedAnswerEngine
from aimf.application.knowledge.answering.protocol import AnswerProvider
from aimf.application.knowledge.embedding.protocol import EmbeddingProvider
from aimf.application.knowledge.queries import KnowledgeQueryService
from aimf.application.knowledge.retrieval import RepositoryRetriever
from aimf.application.knowledge.vector_store import VectorStore
from aimf.config import AimfSettings, McpSettings, McpToolsSettings


@dataclass
class RepositoryIntelligenceContext:
    """Read-only DI bundle for repository-intelligence MCP tools.

    Tools must not construct stores, embeddings, or production AI providers.
    """

    queries: KnowledgeQueryService
    settings: AimfSettings | None = None
    mcp: McpSettings = field(default_factory=McpSettings)
    retriever: RepositoryRetriever | None = None
    answer_engine: GroundedAnswerEngine | None = None
    answer_provider: AnswerProvider | None = None
    embedding_provider: EmbeddingProvider | None = None
    vector_store: VectorStore | None = None
    vector_store_provider: str = "memory"
    vector_store_persistent: bool = False
    composition_diagnostics: tuple[dict[str, Any], ...] = ()

    @property
    def tools(self) -> McpToolsSettings:
        return self.mcp.tools

    def tool_enabled(self, tool_key: str) -> bool:
        return bool(getattr(self.tools, tool_key, False))
