"""In-memory repository adapters for tests and local use."""

from __future__ import annotations

from codestrata_platform.infrastructure.memory.answer_runs import InMemoryAnswerRunRepository
from codestrata_platform.infrastructure.memory.artifacts import InMemoryArtifactRepository
from codestrata_platform.infrastructure.memory.assessments import InMemoryAssessmentRepository
from codestrata_platform.infrastructure.memory.engineering import (
    InMemoryEngineeringSnapshotRepository,
    InMemoryEngineeringTaxonomyRepository,
)
from codestrata_platform.infrastructure.memory.executive_intelligence import (
    InMemoryExecutiveIntelligenceRepository,
)
from codestrata_platform.infrastructure.memory.graph_intelligence import (
    InMemoryGraphIntelligenceRepository,
)
from codestrata_platform.infrastructure.memory.intelligence import (
    InMemoryAssessmentIntelligenceRepository,
    InMemoryFindingRepository,
    InMemoryMetricRepository,
    InMemoryRecommendationRepository,
)
from codestrata_platform.infrastructure.memory.knowledge_graph import (
    InMemoryKnowledgeGraphRepository,
)
from codestrata_platform.infrastructure.memory.organizations import (
    InMemoryOrganizationRepository,
)
from codestrata_platform.infrastructure.memory.portfolio_answer_runs import (
    InMemoryPortfolioAnswerRunRepository,
)
from codestrata_platform.infrastructure.memory.portfolio_retrieval import (
    InMemoryPortfolioRetrievalRepository,
)
from codestrata_platform.infrastructure.memory.portfolios import (
    InMemoryPortfolioRepository,
    InMemoryPortfolioSnapshotRepository,
)
from codestrata_platform.infrastructure.memory.repositories import InMemoryRepositoryRepository
from codestrata_platform.infrastructure.memory.retrieval import InMemoryRetrievalRepository
from codestrata_platform.infrastructure.memory.workspaces import InMemoryWorkspaceRepository

__all__ = [
    "InMemoryAnswerRunRepository",
    "InMemoryArtifactRepository",
    "InMemoryAssessmentIntelligenceRepository",
    "InMemoryAssessmentRepository",
    "InMemoryEngineeringSnapshotRepository",
    "InMemoryEngineeringTaxonomyRepository",
    "InMemoryExecutiveIntelligenceRepository",
    "InMemoryFindingRepository",
    "InMemoryGraphIntelligenceRepository",
    "InMemoryKnowledgeGraphRepository",
    "InMemoryMetricRepository",
    "InMemoryOrganizationRepository",
    "InMemoryPortfolioAnswerRunRepository",
    "InMemoryPortfolioRepository",
    "InMemoryPortfolioRetrievalRepository",
    "InMemoryPortfolioSnapshotRepository",
    "InMemoryRecommendationRepository",
    "InMemoryRepositoryRepository",
    "InMemoryRetrievalRepository",
    "InMemoryWorkspaceRepository",
]
