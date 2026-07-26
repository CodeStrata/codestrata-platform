"""Repository-intelligence MCP tool registry (Phase 5.7).

External MCP tool names use underscores (SDK-friendly). Documented dotted
aliases map 1:1:

  repository.search            → repository_search
  repository.answer            → repository_answer
  repository.findings          → repository_findings
  repository.recommendations   → repository_recommendations
  repository.assessments       → repository_assessments
  repository.files             → repository_files
  repository.architecture      → repository_architecture
  repository.security          → repository_security
  repository.dependencies      → repository_dependencies
  repository.tests             → repository_tests
  repository.cloud             → repository_cloud
  repository.ai_readiness      → repository_ai_readiness
  repository.performance       → repository_performance
  repository.health            → repository_health
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from mcp.server.fastmcp import FastMCP

from aimf.domain.knowledge.identifiers import fingerprint_payload
from aimf.interfaces.mcp.context import RepositoryIntelligenceContext
from aimf.interfaces.mcp.envelope import McpServerManifest

TOOL_VERSION = "1.0.0"

# Dotted external name → registered FastMCP tool name
TOOL_NAME_ALIASES: dict[str, str] = {
    "repository.search": "repository_search",
    "repository.answer": "repository_answer",
    "repository.findings": "repository_findings",
    "repository.recommendations": "repository_recommendations",
    "repository.assessments": "repository_assessments",
    "repository.files": "repository_files",
    "repository.architecture": "repository_architecture",
    "repository.security": "repository_security",
    "repository.dependencies": "repository_dependencies",
    "repository.tests": "repository_tests",
    "repository.cloud": "repository_cloud",
    "repository.ai_readiness": "repository_ai_readiness",
    "repository.performance": "repository_performance",
    "repository.health": "repository_health",
}

REPOSITORY_INTELLIGENCE_TOOLS: tuple[str, ...] = tuple(
    sorted(TOOL_NAME_ALIASES.values())
)

TOOL_SETTING_KEYS: dict[str, str] = {
    "repository_search": "repository_search",
    "repository_answer": "repository_answer",
    "repository_findings": "repository_findings",
    "repository_recommendations": "repository_recommendations",
    "repository_assessments": "repository_assessments",
    "repository_files": "repository_files",
    "repository_architecture": "repository_architecture",
    "repository_security": "repository_security",
    "repository_dependencies": "repository_dependencies",
    "repository_tests": "repository_tests",
    "repository_cloud": "repository_cloud",
    "repository_ai_readiness": "repository_ai_readiness",
    "repository_performance": "repository_performance",
    "repository_health": "repository_health",
}


class ToolRegistryError(ValueError):
    """Raised when tool registration is invalid."""


class RepositoryIntelligenceToolRegistry:
    """Deterministic registration of repository-intelligence MCP tools."""

    def __init__(self) -> None:
        self._registered: list[str] = []
        self._versions: dict[str, str] = {}

    @property
    def registered_tools(self) -> tuple[str, ...]:
        return tuple(self._registered)

    def register(
        self,
        name: str,
        *,
        version: str = TOOL_VERSION,
        enabled: bool = True,
    ) -> bool:
        if name in self._registered:
            raise ToolRegistryError(f"duplicate MCP tool registration: {name}")
        if not enabled:
            return False
        self._registered.append(name)
        self._versions[name] = version
        return True

    def manifest(
        self,
        *,
        server_name: str,
        server_version: str,
        transport: str,
    ) -> McpServerManifest:
        tools = tuple(sorted(self._registered))
        versions = {name: self._versions[name] for name in tools}
        fingerprint = fingerprint_payload(
            {
                "server_name": server_name,
                "server_version": server_version,
                "transport": transport,
                "tools": list(tools),
                "versions": versions,
            }
        )
        return McpServerManifest(
            server_name=server_name,
            server_version=server_version,
            transport=transport,
            tools=tools,
            tool_versions=versions,
            fingerprint=fingerprint,
        )


def register_repository_intelligence_tools(
    server: FastMCP,
    context: RepositoryIntelligenceContext,
    *,
    registry: RepositoryIntelligenceToolRegistry | None = None,
) -> RepositoryIntelligenceToolRegistry:
    """Register Phase 5.7 tools when enabled in [mcp.tools]."""

    from aimf.interfaces.mcp.tools import repository_intelligence as ri

    reg = registry or RepositoryIntelligenceToolRegistry()
    registrars: Sequence[tuple[str, Callable[..., None]]] = (
        ("repository_search", ri.register_repository_search),
        ("repository_answer", ri.register_repository_answer),
        ("repository_findings", ri.register_repository_findings),
        ("repository_recommendations", ri.register_repository_recommendations),
        ("repository_assessments", ri.register_repository_assessments),
        ("repository_files", ri.register_repository_files),
        ("repository_architecture", ri.register_pack_architecture),
        ("repository_security", ri.register_pack_security),
        ("repository_dependencies", ri.register_pack_dependencies),
        ("repository_tests", ri.register_pack_tests),
        ("repository_cloud", ri.register_pack_cloud),
        ("repository_ai_readiness", ri.register_pack_ai_readiness),
        ("repository_performance", ri.register_pack_performance),
        ("repository_health", ri.register_repository_health),
    )
    for tool_name, registrar in registrars:
        setting_key = TOOL_SETTING_KEYS[tool_name]
        if not context.tool_enabled(setting_key):
            continue
        if reg.register(tool_name, enabled=True):
            registrar(server, context)
    return reg
