"""API controller package."""

from __future__ import annotations

from fastapi import APIRouter

from codestrata_platform.api.answering import router as answering_router
from codestrata_platform.api.controllers.assessments import router as assessments_router
from codestrata_platform.api.controllers.engineering import router as engineering_router
from codestrata_platform.api.controllers.intelligence import router as intelligence_router
from codestrata_platform.api.controllers.organizations import router as organizations_router
from codestrata_platform.api.controllers.repositories import router as repositories_router
from codestrata_platform.api.controllers.workspaces import router as workspaces_router
from codestrata_platform.api.ingestion.artifacts import router as ingestion_artifacts_router
from codestrata_platform.api.ingestion.controllers import router as ingestion_router
from codestrata_platform.api.ingestion.intelligence import router as ingestion_intelligence_router
from codestrata_platform.api.knowledge_graph import router as knowledge_graph_router
from codestrata_platform.api.portfolio import router as portfolio_router
from codestrata_platform.api.portfolio_answering import router as portfolio_answering_router
from codestrata_platform.api.portfolio_retrieval import router as portfolio_retrieval_router
from codestrata_platform.api.retrieval import router as retrieval_router


def build_api_router() -> APIRouter:
    api = APIRouter(prefix="/api/v1")
    api.include_router(organizations_router)
    api.include_router(workspaces_router)
    api.include_router(repositories_router)
    api.include_router(assessments_router)
    api.include_router(intelligence_router)
    api.include_router(engineering_router)
    api.include_router(knowledge_graph_router)
    api.include_router(retrieval_router)
    api.include_router(answering_router)
    api.include_router(portfolio_router)
    api.include_router(portfolio_retrieval_router)
    api.include_router(portfolio_answering_router)
    api.include_router(ingestion_router)
    api.include_router(ingestion_artifacts_router)
    api.include_router(ingestion_intelligence_router)
    return api
