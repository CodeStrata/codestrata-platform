"""Durable persistence adapters for Commercial Platform repository ports.

Infrastructure-only. Domain and Application must not import this package.
"""

from __future__ import annotations

from codestrata_platform.infrastructure.persistence.database import (
    create_engine_from_url,
    create_platform_schema,
    create_session_factory,
    get_database_url,
)
from codestrata_platform.infrastructure.persistence.repositories import (
    SqlAlchemyAssessmentArtifactRepository,
    SqlAlchemyAssessmentIntelligenceRepository,
    SqlAlchemyAssessmentRepository,
    SqlAlchemyEngineeringSnapshotRepository,
    SqlAlchemyFindingRepository,
    SqlAlchemyGraphIntelligenceRepository,
    SqlAlchemyKnowledgeGraphRepository,
    SqlAlchemyMetricRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyPortfolioQueryRepository,
    SqlAlchemyPortfolioRepository,
    SqlAlchemyPortfolioRetrievalRepository,
    SqlAlchemyPortfolioSnapshotRepository,
    SqlAlchemyRecommendationRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyRetrievalIndexRepository,
    SqlAlchemyWorkspaceRepository,
)
from codestrata_platform.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

__all__ = [
    "SqlAlchemyAssessmentArtifactRepository",
    "SqlAlchemyAssessmentIntelligenceRepository",
    "SqlAlchemyAssessmentRepository",
    "SqlAlchemyEngineeringSnapshotRepository",
    "SqlAlchemyFindingRepository",
    "SqlAlchemyGraphIntelligenceRepository",
    "SqlAlchemyKnowledgeGraphRepository",
    "SqlAlchemyMetricRepository",
    "SqlAlchemyOrganizationRepository",
    "SqlAlchemyPortfolioQueryRepository",
    "SqlAlchemyPortfolioRepository",
    "SqlAlchemyPortfolioRetrievalRepository",
    "SqlAlchemyPortfolioSnapshotRepository",
    "SqlAlchemyRecommendationRepository",
    "SqlAlchemyRepositoryRepository",
    "SqlAlchemyRetrievalIndexRepository",
    "SqlAlchemyUnitOfWork",
    "SqlAlchemyWorkspaceRepository",
    "create_engine_from_url",
    "create_platform_schema",
    "create_session_factory",
    "get_database_url",
]
