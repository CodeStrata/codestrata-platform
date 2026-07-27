"""Commands for graph intelligence (optional cache invalidation hooks)."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId


@dataclass(frozen=True, slots=True)
class InvalidateGraphAnalysisCacheCommand:
    graph_id: KnowledgeGraphId
