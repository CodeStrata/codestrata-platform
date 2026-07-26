"""Register Platform MCP tools/resources on a Community FastMCP server."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from codestrata.config import CodestrataSettings
from codestrata.interfaces.mcp.context import RepositoryIntelligenceContext


def register_platform_mcp(
    server: FastMCP,
    *,
    queries: Any,
    settings: CodestrataSettings | None = None,
    enterprise_knowledge_service: Any | None = None,
    enterprise_query_service: Any | None = None,
    repository_intelligence: RepositoryIntelligenceContext | None = None,
    **_: Any,
) -> None:
    """Register Knowledge Graph and RAG MCP surfaces when Platform is installed."""

    from codestrata_platform.knowledge_graph.mcp.resources_enterprise import (
        register_enterprise_resources,
    )
    from codestrata_platform.knowledge_graph.mcp.tools_enterprise import (
        register_enterprise_tools,
    )
    from codestrata_platform.rag.mcp.composition import compose_repository_intelligence
    from codestrata_platform.rag.mcp.registry import register_repository_intelligence_tools

    register_enterprise_tools(
        server,
        knowledge_service=enterprise_knowledge_service,
        query_service=enterprise_query_service,
    )
    if enterprise_query_service is not None:
        register_enterprise_resources(server, query_service=enterprise_query_service)

    ri = repository_intelligence
    if ri is None and queries is not None:
        ri = compose_repository_intelligence(
            queries=queries,
            settings=settings,
            mcp_settings=settings.mcp if settings is not None else None,
        )
    if ri is not None:
        register_repository_intelligence_tools(server, ri)
