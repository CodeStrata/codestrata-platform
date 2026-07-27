"""SqlAlchemy GraphIntelligenceRepository adapter."""

from __future__ import annotations

from codestrata_platform.domain.knowledge_graph.ports import KnowledgeGraphRepository
from codestrata_platform.infrastructure.graph_intelligence import GraphIntelligenceRepositoryBase


class SqlAlchemyGraphIntelligenceRepository(GraphIntelligenceRepositoryBase):
    def __init__(self, graphs: KnowledgeGraphRepository) -> None:
        super().__init__(graphs)
