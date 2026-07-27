"""API package for Engineering Knowledge Graph."""

from __future__ import annotations

from fastapi import APIRouter

from codestrata_platform.api.knowledge_graph.controllers import router as graph_router
from codestrata_platform.api.knowledge_graph.intelligence_controllers import (
    router as intelligence_router,
)

router = APIRouter()
router.include_router(graph_router)
router.include_router(intelligence_router)

__all__ = ["router"]
