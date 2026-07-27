"""SQLAlchemy repository adapters implementing Domain ports."""

from __future__ import annotations

from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_answer_run_repository import (  # noqa: E501
    SqlAlchemyAnswerRunRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_assessment_artifact_repository import (  # noqa: E501
    SqlAlchemyAssessmentArtifactRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_assessment_intelligence_repository import (  # noqa: E501
    SqlAlchemyAssessmentIntelligenceRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_assessment_repository import (  # noqa: E501
    SqlAlchemyAssessmentRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_engineering_snapshot_repository import (  # noqa: E501
    SqlAlchemyEngineeringSnapshotRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_executive_intelligence_repository import (  # noqa: E501
    SqlAlchemyExecutiveIntelligenceRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_finding_repository import (  # noqa: E501
    SqlAlchemyFindingRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_graph_intelligence_repository import (  # noqa: E501
    SqlAlchemyGraphIntelligenceRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_knowledge_graph_repository import (  # noqa: E501
    SqlAlchemyKnowledgeGraphRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (  # noqa: E501
    SqlAlchemyMetricRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_organization_repository import (  # noqa: E501
    SqlAlchemyOrganizationRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_portfolio_answer_run_repository import (  # noqa: E501
    SqlAlchemyPortfolioAnswerRunRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_portfolio_repository import (  # noqa: E501
    SqlAlchemyPortfolioQueryRepository,
    SqlAlchemyPortfolioRepository,
    SqlAlchemyPortfolioSnapshotRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_portfolio_retrieval_repository import (  # noqa: E501
    SqlAlchemyPortfolioRetrievalRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_recommendation_repository import (  # noqa: E501
    SqlAlchemyRecommendationRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_repository_repository import (  # noqa: E501
    SqlAlchemyRepositoryRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_retrieval_index_repository import (  # noqa: E501
    SqlAlchemyRetrievalIndexRepository,
)
from codestrata_platform.infrastructure.persistence.repositories.sqlalchemy_workspace_repository import (  # noqa: E501
    SqlAlchemyWorkspaceRepository,
)

__all__ = [
    "SqlAlchemyAnswerRunRepository",
    "SqlAlchemyAssessmentArtifactRepository",
    "SqlAlchemyAssessmentIntelligenceRepository",
    "SqlAlchemyAssessmentRepository",
    "SqlAlchemyEngineeringSnapshotRepository",
    "SqlAlchemyExecutiveIntelligenceRepository",
    "SqlAlchemyFindingRepository",
    "SqlAlchemyGraphIntelligenceRepository",
    "SqlAlchemyKnowledgeGraphRepository",
    "SqlAlchemyMetricRepository",
    "SqlAlchemyOrganizationRepository",
    "SqlAlchemyPortfolioAnswerRunRepository",
    "SqlAlchemyPortfolioQueryRepository",
    "SqlAlchemyPortfolioRepository",
    "SqlAlchemyPortfolioRetrievalRepository",
    "SqlAlchemyPortfolioSnapshotRepository",
    "SqlAlchemyRecommendationRepository",
    "SqlAlchemyRepositoryRepository",
    "SqlAlchemyRetrievalIndexRepository",
    "SqlAlchemyWorkspaceRepository",
]
