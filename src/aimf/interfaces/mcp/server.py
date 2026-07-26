"""FastMCP server construction for CodeStrata."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from aimf import __version__ as PACKAGE_VERSION
from aimf.application.agents import AgentOrchestrator
from aimf.application.assessment import AssessmentApplicationService
from aimf.application.enterprise.query_service import EnterpriseKnowledgeQueryService
from aimf.application.knowledge.queries import KnowledgeQueryService
from aimf.config import AimfSettings
from aimf.interfaces.mcp.context import RepositoryIntelligenceContext
from aimf.interfaces.mcp.prompts import register_prompts
from aimf.interfaces.mcp.registry import RepositoryIntelligenceToolRegistry
from aimf.interfaces.mcp.resources import register_resources
from aimf.interfaces.mcp.tools import register_all_tools

CODESSTRATA_MCP_NAME = "CodeStrata"
CODESSTRATA_MCP_INSTRUCTIONS = (
    "CodeStrata modernization knowledge server. Query durable assessment "
    "knowledge, repository retrieval, and grounded answers. Prefer list/get/"
    "explain tools for precise queries; use repository_* tools for scoped "
    "repository intelligence. repository_answer uses deterministic extractive "
    "answering (not generative AI). Agents should call application services "
    "directly rather than nesting through this MCP server."
)


def build_mcp_server(
    *,
    queries: KnowledgeQueryService,
    assessment_service: AssessmentApplicationService,
    settings: AimfSettings | None = None,
    agent_orchestrator: AgentOrchestrator | None = None,
    incremental_operations: object | None = None,
    incremental_inspection: object | None = None,
    enterprise_knowledge_service: object | None = None,
    enterprise_query_service: object | None = None,
    rule_analysis_service: object | None = None,
    language_evidence_service: object | None = None,
    architecture_conclusion_service: object | None = None,
    repository_intelligence: RepositoryIntelligenceContext | None = None,
) -> FastMCP:
    """Assemble a FastMCP server with tools, resources, and prompts registered."""

    mcp_settings = settings.mcp if settings is not None else None
    host = mcp_settings.host if mcp_settings is not None else "127.0.0.1"
    port = mcp_settings.port if mcp_settings is not None else 8765
    log_level = mcp_settings.log_level if mcp_settings is not None else "INFO"
    server_name = (
        (mcp_settings.server_name if mcp_settings is not None else None)
        or CODESSTRATA_MCP_NAME
    )

    server = FastMCP(
        name=server_name,
        instructions=CODESSTRATA_MCP_INSTRUCTIONS,
        host=host,
        port=port,
        log_level=log_level,  # type: ignore[arg-type]
    )
    evidence_service = language_evidence_service
    if evidence_service is None:
        from aimf.application.evidence.language.factory import create_language_evidence_service

        evidence_service = create_language_evidence_service(settings)

    conclusion_service = architecture_conclusion_service
    if conclusion_service is None:
        from aimf.application.architecture.conclusions.factory import (
            create_architecture_conclusion_service,
        )

        conclusion_service = create_architecture_conclusion_service(settings)

    ri_registry = register_all_tools(
        server,
        queries=queries,
        assessment_service=assessment_service,
        settings=settings,
        agent_orchestrator=agent_orchestrator,
        incremental_operations=incremental_operations,
        incremental_inspection=incremental_inspection,
        enterprise_knowledge_service=enterprise_knowledge_service,
        enterprise_query_service=enterprise_query_service,
        rule_analysis_service=rule_analysis_service,
        language_evidence_service=evidence_service,
        architecture_conclusion_service=conclusion_service,
        repository_intelligence=repository_intelligence,
    )
    enterprise_queries = (
        enterprise_query_service
        if isinstance(enterprise_query_service, EnterpriseKnowledgeQueryService)
        else None
    )
    register_resources(
        server,
        queries,
        enterprise_query_service=enterprise_queries,
        repository_intelligence=repository_intelligence,
    )
    register_prompts(server, queries)

    if isinstance(ri_registry, RepositoryIntelligenceToolRegistry):
        version = (
            (mcp_settings.server_version if mcp_settings is not None else None)
            or PACKAGE_VERSION
        )
        transport = mcp_settings.transport if mcp_settings is not None else "stdio"
        server._codestrata_ri_registry = ri_registry  # noqa: SLF001
        server._codestrata_manifest = ri_registry.manifest(  # noqa: SLF001
            server_name=server_name,
            server_version=version,
            transport=transport,
        )
        server._codestrata_repository_intelligence = repository_intelligence  # noqa: SLF001
    return server
