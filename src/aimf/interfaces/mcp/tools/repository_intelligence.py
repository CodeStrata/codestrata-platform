"""Repository-intelligence MCP tools (Phase 5.7).

Thin adapters over RepositoryRetriever, GroundedAnswerEngine, and
KnowledgeQueryService. No assessment/retrieval/answering business logic here.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from aimf import __version__ as PACKAGE_VERSION
from aimf.domain.knowledge.answering import AnswerStyle, GroundedAnswerRequest
from aimf.domain.knowledge.identifiers import fingerprint_payload
from aimf.domain.knowledge.retrieval import RetrievalRequest
from aimf.interfaces.mcp.context import RepositoryIntelligenceContext
from aimf.interfaces.mcp.envelope import McpDiagnostic, McpHealthResponse, McpToolStatus
from aimf.interfaces.mcp.mapping import to_mcp_payload
from aimf.interfaces.mcp.security import optional_filter, require_nonblank
from aimf.interfaces.mcp.tools._common import (
    FINDINGS_DEFAULT,
    FINDINGS_MAX,
    RECOMMENDATIONS_DEFAULT,
    RECOMMENDATIONS_MAX,
    clamp_tool_limit,
    run_bounded,
)
from aimf.interfaces.mcp.tools.repository_common import (
    DEFAULT_LIMITATIONS,
    bound_payload,
    build_filters,
    build_scope,
    disabled_response,
    failed_response,
    filter_findings,
    filter_recommendations,
    map_answer_status,
    map_retrieval_status,
    resolve_latest_run_id,
    strip_embeddings,
)
from aimf.security.database_url import sanitize_exception_message


def _max_chars(context: RepositoryIntelligenceContext) -> int:
    return context.mcp.max_result_characters


def register_repository_search(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    @server.tool(name="repository_search", structured_output=True)
    def repository_search(
        query: str,
        tenant_id: str,
        repository_id: str,
        scan_id: str | None = None,
        branch: str | None = None,
        commit_sha: str | None = None,
        source_types: list[str] | None = None,
        intelligence_packs: list[str] | None = None,
        severities: list[str] | None = None,
        file_paths: list[str] | None = None,
        top_k: int = 10,
        candidate_limit: int = 30,
        minimum_score: float = 0.0,
        include_content: bool = True,
        include_metadata: bool = True,
        include_traceability: bool = True,
    ) -> dict[str, Any]:
        """Search indexed repository knowledge (delegates to RepositoryRetriever)."""

        def _run() -> dict[str, Any]:
            request_payload = {
                "query": query,
                "tenant_id": tenant_id,
                "repository_id": repository_id,
                "scan_id": scan_id,
                "top_k": top_k,
            }
            settings = context.settings
            if settings is not None and not settings.knowledge.retrieval.enabled:
                return disabled_response(
                    "repository_search",
                    code="retrieval_disabled",
                    message="knowledge.retrieval.enabled is false",
                    request_payload=request_payload,
                )
            if context.retriever is None:
                return failed_response(
                    "repository_search",
                    code="provider_unavailable",
                    message="repository retriever is unavailable",
                    request_payload=request_payload,
                )
            scope = build_scope(
                tenant_id=tenant_id,
                repository_id=repository_id,
                scan_id=scan_id,
                branch=branch,
                commit_sha=commit_sha,
            )
            filters = build_filters(
                source_types=source_types,
                intelligence_packs=intelligence_packs,
                severities=severities,
                file_paths=file_paths,
            )
            result = context.retriever.retrieve(
                RetrievalRequest(
                    query=require_nonblank(query, label="query"),
                    scope=scope,
                    filters=filters,
                    top_k=max(1, int(top_k)),
                    candidate_limit=max(1, int(candidate_limit)),
                    minimum_score=float(minimum_score),
                    include_content=include_content,
                    include_metadata=include_metadata,
                    include_traceability=(
                        include_traceability and context.mcp.include_traceability
                    ),
                )
            )
            hits = [
                strip_embeddings(hit.model_dump(mode="json"))
                for hit in result.context.hits
            ]
            data = {
                "status": result.status.value,
                "normalized_query": result.query.normalized if result.query else None,
                "query_fingerprint": result.query.fingerprint if result.query else None,
                "citation_labels": list(result.context.citation_labels),
                "hits": hits,
                "coverage": result.coverage.model_dump(mode="json"),
                "limitations": list(result.limitations),
            }
            if context.mcp.include_diagnostics:
                data["diagnostics"] = [
                    item.model_dump(mode="json") for item in result.diagnostics
                ]
            return bound_payload(
                "repository_search",
                status=map_retrieval_status(result.status),
                data=data,
                request_payload=request_payload,
                max_characters=_max_chars(context),
                result_count=len(hits),
                limitations=DEFAULT_LIMITATIONS,
            )

        return run_bounded("repository_search", _run)


def register_repository_answer(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    @server.tool(name="repository_answer", structured_output=True)
    def repository_answer(
        question: str,
        tenant_id: str,
        repository_id: str,
        scan_id: str | None = None,
        branch: str | None = None,
        commit_sha: str | None = None,
        source_types: list[str] | None = None,
        answer_style: str = "concise",
        top_k: int = 10,
        max_statements: int = 20,
        max_answer_characters: int = 12_000,
        include_evidence: bool = True,
        include_retrieval_context: bool = False,
        include_diagnostics: bool = True,
    ) -> dict[str, Any]:
        """Answer a repository question with citation-bound grounded evidence.

        Uses DeterministicExtractiveAnswerProvider (non-generative, non-production).
        """

        def _run() -> dict[str, Any]:
            request_payload = {
                "question": question,
                "tenant_id": tenant_id,
                "repository_id": repository_id,
                "answer_style": answer_style,
            }
            settings = context.settings
            if settings is not None and not settings.knowledge.answering.enabled:
                return disabled_response(
                    "repository_answer",
                    code="answering_disabled",
                    message="knowledge.answering.enabled is false",
                    request_payload=request_payload,
                )
            if settings is not None and not settings.knowledge.retrieval.enabled:
                return disabled_response(
                    "repository_answer",
                    code="retrieval_disabled",
                    message="knowledge.retrieval.enabled is false",
                    request_payload=request_payload,
                )
            if context.answer_engine is None:
                return failed_response(
                    "repository_answer",
                    code="provider_unavailable",
                    message="grounded answer engine is unavailable",
                    request_payload=request_payload,
                )
            try:
                style = AnswerStyle(answer_style.strip().lower())
            except ValueError as error:
                raise ValueError(
                    "answer_style must be one of: concise, detailed, "
                    "findings_summary, recommendation_summary, "
                    "architecture_explanation, evidence_only"
                ) from error
            scope = build_scope(
                tenant_id=tenant_id,
                repository_id=repository_id,
                scan_id=scan_id,
                branch=branch,
                commit_sha=commit_sha,
            )
            result = context.answer_engine.answer(
                GroundedAnswerRequest(
                    question=require_nonblank(question, label="question"),
                    scope=scope,
                    filters=build_filters(source_types=source_types),
                    top_k=max(1, int(top_k)),
                    style=style,
                    max_statements=max(1, int(max_statements)),
                    max_answer_characters=max(1, int(max_answer_characters)),
                    include_evidence=include_evidence,
                    include_retrieval_context=include_retrieval_context,
                    include_diagnostics=include_diagnostics
                    and context.mcp.include_diagnostics,
                )
            )
            answer = result.answer
            provider = (
                answer.provider.model_dump(mode="json")
                if answer is not None
                else (
                    context.answer_provider.model_identity().model_dump(mode="json")
                    if context.answer_provider is not None
                    else {}
                )
            )
            data: dict[str, Any] = {
                "answer_status": result.status.value,
                "summary": answer.summary if answer else None,
                "sections": (
                    [section.model_dump(mode="json") for section in answer.sections]
                    if answer
                    else []
                ),
                "statements": (
                    [item.model_dump(mode="json") for item in answer.statements]
                    if answer
                    else []
                ),
                "citations": (
                    [item.model_dump(mode="json") for item in answer.citations]
                    if answer
                    else []
                ),
                "confidence": answer.confidence.value if answer else None,
                "coverage": result.coverage.model_dump(mode="json"),
                "provider": provider,
                "provider_notes": {
                    "is_generative_ai": False,
                    "is_production_model": False,
                    "mode": "deterministic_extractive",
                    "label": (
                        "Deterministic extractive answering for tests/dogfood; "
                        "not an LLM-generated answer."
                    ),
                },
            }
            if include_evidence:
                data["evidence"] = [
                    item.model_dump(mode="json") for item in result.evidence
                ]
            if include_diagnostics and context.mcp.include_diagnostics:
                data["diagnostics"] = [
                    item.model_dump(mode="json") for item in result.diagnostics
                ]
            data["limitations"] = [
                item.message if hasattr(item, "message") else str(item)
                for item in result.limitations
            ]
            return bound_payload(
                "repository_answer",
                status=map_answer_status(result.status),
                data=strip_embeddings(data),
                request_payload=request_payload,
                max_characters=_max_chars(context),
                result_count=len(data.get("statements") or []),
                limitations=DEFAULT_LIMITATIONS,
            )

        return run_bounded("repository_answer", _run)


def _assessment_items(
    context: RepositoryIntelligenceContext,
    *,
    repository_id: str,
    intelligence_pack: str | None,
    severity: str | None,
    finding_id: str | None,
    rule_id: str | None,
    file_path: str | None,
    result_limit: int,
    kind: str,
) -> tuple[str | None, list[Any], bool]:
    run_id = resolve_latest_run_id(context.queries, repository_id)
    if run_id is None:
        return None, [], False
    items: list[Any]
    if kind == "findings":
        items = filter_findings(
            context.queries.get_findings(run_id),
            intelligence_pack=intelligence_pack,
            severity=severity,
            finding_id=finding_id,
            rule_id=rule_id,
            file_path=file_path,
        )
        capped = clamp_tool_limit(
            result_limit,
            default=FINDINGS_DEFAULT,
            maximum=FINDINGS_MAX,
            label="findings",
        )
    else:
        items = filter_recommendations(
            context.queries.get_recommendations(run_id),
            intelligence_pack=intelligence_pack,
            severity=severity,
            finding_id=finding_id,
        )
        capped = clamp_tool_limit(
            result_limit,
            default=RECOMMENDATIONS_DEFAULT,
            maximum=RECOMMENDATIONS_MAX,
            label="recommendations",
        )
    truncated = len(items) > capped
    return run_id, items[:capped], truncated


def register_repository_findings(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    @server.tool(name="repository_findings", structured_output=True)
    def repository_findings(
        tenant_id: str,
        repository_id: str,
        scan_id: str | None = None,
        intelligence_pack: str | None = None,
        severity: str | None = None,
        finding_id: str | None = None,
        rule_id: str | None = None,
        file_path: str | None = None,
        result_limit: int = FINDINGS_DEFAULT,
    ) -> dict[str, Any]:
        """Return assessment findings for a repository scope."""

        def _run() -> dict[str, Any]:
            tenant, repo = (
                require_nonblank(tenant_id, label="tenant_id"),
                require_nonblank(repository_id, label="repository_id"),
            )
            request_payload = {
                "tenant_id": tenant,
                "repository_id": repo,
                "intelligence_pack": intelligence_pack,
                "severity": severity,
            }
            try:
                run_id, items, truncated = _assessment_items(
                    context,
                    repository_id=repo,
                    intelligence_pack=intelligence_pack,
                    severity=severity,
                    finding_id=finding_id,
                    rule_id=rule_id,
                    file_path=file_path,
                    result_limit=result_limit,
                    kind="findings",
                )
            except Exception as exc:  # noqa: BLE001
                return failed_response(
                    "repository_findings",
                    code="upstream_failure",
                    message=sanitize_exception_message(str(exc)),
                    request_payload=request_payload,
                )
            status = (
                McpToolStatus.EMPTY
                if not items
                else McpToolStatus.PARTIAL
                if truncated
                else McpToolStatus.SUCCESS
            )
            data = {
                "tenant_id": tenant,
                "repository_id": repo,
                "run_id": run_id,
                "findings": [to_mcp_payload(item) for item in items],
            }
            return bound_payload(
                "repository_findings",
                status=status,
                data=data,
                request_payload=request_payload,
                max_characters=_max_chars(context),
                result_count=len(items),
                diagnostics=(
                    (
                        McpDiagnostic(
                            code="result_limit",
                            message="findings truncated to result_limit",
                            severity="info",
                        ),
                    )
                    if truncated
                    else ()
                ),
            )

        return run_bounded("repository_findings", _run)


def register_repository_recommendations(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    @server.tool(name="repository_recommendations", structured_output=True)
    def repository_recommendations(
        tenant_id: str,
        repository_id: str,
        scan_id: str | None = None,
        intelligence_pack: str | None = None,
        severity: str | None = None,
        finding_id: str | None = None,
        result_limit: int = RECOMMENDATIONS_DEFAULT,
    ) -> dict[str, Any]:
        """Return recommendations for a repository scope."""

        def _run() -> dict[str, Any]:
            tenant, repo = (
                require_nonblank(tenant_id, label="tenant_id"),
                require_nonblank(repository_id, label="repository_id"),
            )
            request_payload = {
                "tenant_id": tenant,
                "repository_id": repo,
                "intelligence_pack": intelligence_pack,
            }
            run_id, items, truncated = _assessment_items(
                context,
                repository_id=repo,
                intelligence_pack=intelligence_pack,
                severity=severity,
                finding_id=finding_id,
                rule_id=None,
                file_path=None,
                result_limit=result_limit,
                kind="recommendations",
            )
            status = (
                McpToolStatus.EMPTY
                if not items
                else McpToolStatus.PARTIAL
                if truncated
                else McpToolStatus.SUCCESS
            )
            data = {
                "tenant_id": tenant,
                "repository_id": repo,
                "run_id": run_id,
                "recommendations": [to_mcp_payload(item) for item in items],
            }
            return bound_payload(
                "repository_recommendations",
                status=status,
                data=data,
                request_payload=request_payload,
                max_characters=_max_chars(context),
                result_count=len(items),
            )

        return run_bounded("repository_recommendations", _run)


def register_repository_assessments(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    @server.tool(name="repository_assessments", structured_output=True)
    def repository_assessments(
        tenant_id: str,
        repository_id: str,
        scan_id: str | None = None,
        intelligence_packs: list[str] | None = None,
        include_inventory: bool = False,
        include_limitations: bool = True,
        include_diagnostics: bool = True,
    ) -> dict[str, Any]:
        """Return available repository assessment summaries."""

        def _run() -> dict[str, Any]:
            tenant, repo = (
                require_nonblank(tenant_id, label="tenant_id"),
                require_nonblank(repository_id, label="repository_id"),
            )
            request_payload = {"tenant_id": tenant, "repository_id": repo}
            try:
                runs = context.queries.list_assessment_runs(repo)
                latest = context.queries.get_latest_completed_run(repo)
            except Exception:  # noqa: BLE001
                runs = ()
                latest = None
            packs = sorted({*(intelligence_packs or ())})
            findings_count = 0
            recommendations_count = 0
            if latest is not None:
                findings_count = len(context.queries.get_findings(latest.run_id))
                recommendations_count = len(
                    context.queries.get_recommendations(latest.run_id)
                )
            data: dict[str, Any] = {
                "tenant_id": tenant,
                "repository_id": repo,
                "available_packs": packs
                or sorted(
                    [
                        "architecture",
                        "security",
                        "dependencies",
                        "tests",
                        "cloud",
                        "ai_readiness",
                        "performance",
                    ]
                ),
                "assessment_count": len(runs),
                "latest_run": to_mcp_payload(latest) if latest else None,
                "finding_counts": findings_count,
                "recommendation_counts": recommendations_count,
            }
            if include_inventory:
                data["runs"] = [to_mcp_payload(item) for item in runs[:50]]
            if include_limitations:
                data["limitations"] = list(DEFAULT_LIMITATIONS)
            if include_diagnostics and context.mcp.include_diagnostics:
                data["diagnostics"] = list(context.composition_diagnostics)
            status = McpToolStatus.EMPTY if latest is None else McpToolStatus.SUCCESS
            return bound_payload(
                "repository_assessments",
                status=status,
                data=data,
                request_payload=request_payload,
                max_characters=_max_chars(context),
                result_count=len(runs),
            )

        return run_bounded("repository_assessments", _run)


def register_repository_files(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    @server.tool(name="repository_files", structured_output=True)
    def repository_files(
        tenant_id: str,
        repository_id: str,
        scan_id: str | None = None,
        file_path: str | None = None,
        language: str | None = None,
        framework: str | None = None,
        symbol_name: str | None = None,
        result_limit: int = 20,
        include_content: bool = False,
    ) -> dict[str, Any]:
        """Return indexed repository file knowledge (no arbitrary filesystem access)."""

        def _run() -> dict[str, Any]:
            request_payload = {
                "tenant_id": tenant_id,
                "repository_id": repository_id,
                "file_path": file_path,
            }
            settings = context.settings
            if settings is not None and not settings.knowledge.retrieval.enabled:
                return disabled_response(
                    "repository_files",
                    code="retrieval_disabled",
                    message="knowledge.retrieval.enabled is false",
                    request_payload=request_payload,
                )
            if context.retriever is None:
                return failed_response(
                    "repository_files",
                    code="provider_unavailable",
                    message="repository retriever is unavailable",
                    request_payload=request_payload,
                )
            path = optional_filter(file_path, label="file_path")
            query = path or symbol_name or language or framework or "repository file"
            scope = build_scope(
                tenant_id=tenant_id,
                repository_id=repository_id,
                scan_id=scan_id,
            )
            filters = build_filters(
                source_types=("repository_file",),
                file_paths=(path,) if path else (),
                symbol_names=(symbol_name,) if symbol_name else (),
            )
            result = context.retriever.retrieve(
                RetrievalRequest(
                    query=require_nonblank(query, label="query"),
                    scope=scope,
                    filters=filters,
                    top_k=max(1, min(int(result_limit), 50)),
                    include_content=include_content,
                    include_metadata=True,
                    include_traceability=context.mcp.include_traceability,
                )
            )
            files = []
            for hit in result.context.hits:
                if language and (hit.metadata or {}).get("language") != language:
                    continue
                if framework and (hit.metadata or {}).get("framework") != framework:
                    continue
                entry = {
                    "file_path": hit.file_path,
                    "symbol_name": hit.symbol_name,
                    "chunk_id": hit.chunk_id,
                    "document_id": hit.document_id,
                    "scan_id": hit.scan_id,
                    "commit_sha": hit.commit_sha,
                    "citation_label": hit.citation_label,
                    "language": (hit.metadata or {}).get("language"),
                    "framework": (hit.metadata or {}).get("framework"),
                }
                if include_content:
                    entry["content"] = hit.content
                if context.mcp.include_traceability:
                    entry["traceability"] = hit.traceability
                files.append(entry)
            status = map_retrieval_status(result.status)
            if not files and status == McpToolStatus.SUCCESS:
                status = McpToolStatus.EMPTY
            return bound_payload(
                "repository_files",
                status=status,
                data={
                    "tenant_id": scope.tenant_id,
                    "repository_id": scope.repository_id,
                    "files": files,
                },
                request_payload=request_payload,
                max_characters=_max_chars(context),
                result_count=len(files),
            )

        return run_bounded("repository_files", _run)


def _register_pack_tool(
    server: FastMCP,
    context: RepositoryIntelligenceContext,
    *,
    tool_name: str,
    pack: str,
    description: str,
) -> None:
    def _handler(
        tenant_id: str,
        repository_id: str,
        scan_id: str | None = None,
        result_limit: int = 50,
        include_findings: bool = True,
        include_recommendations: bool = True,
        include_evidence: bool = False,
        include_traceability: bool = True,
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            tenant, repo = (
                require_nonblank(tenant_id, label="tenant_id"),
                require_nonblank(repository_id, label="repository_id"),
            )
            request_payload = {
                "tenant_id": tenant,
                "repository_id": repo,
                "pack": pack,
            }
            run_id = resolve_latest_run_id(context.queries, repo)
            findings: list[Any] = []
            recommendations: list[Any] = []
            if run_id is not None and include_findings:
                _, findings, _ = _assessment_items(
                    context,
                    repository_id=repo,
                    intelligence_pack=pack,
                    severity=None,
                    finding_id=None,
                    rule_id=None,
                    file_path=None,
                    result_limit=result_limit,
                    kind="findings",
                )
            if run_id is not None and include_recommendations:
                _, recommendations, _ = _assessment_items(
                    context,
                    repository_id=repo,
                    intelligence_pack=pack,
                    severity=None,
                    finding_id=None,
                    rule_id=None,
                    file_path=None,
                    result_limit=result_limit,
                    kind="recommendations",
                )
            data: dict[str, Any] = {
                "tenant_id": tenant,
                "repository_id": repo,
                "intelligence_pack": pack,
                "run_id": run_id,
                "posture": "available" if run_id else "unavailable",
                "finding_count": len(findings),
                "recommendation_count": len(recommendations),
                "findings": [to_mcp_payload(item) for item in findings]
                if include_findings
                else [],
                "recommendations": [to_mcp_payload(item) for item in recommendations]
                if include_recommendations
                else [],
            }
            if not include_evidence:
                for item in data["findings"]:
                    if isinstance(item, dict):
                        item.pop("evidence", None)
                for item in data["recommendations"]:
                    if isinstance(item, dict):
                        item.pop("evidence", None)
            status = (
                McpToolStatus.EMPTY
                if run_id is None
                else McpToolStatus.SUCCESS
                if findings or recommendations
                else McpToolStatus.EMPTY
            )
            return bound_payload(
                tool_name,
                status=status,
                data=data,
                request_payload=request_payload,
                max_characters=_max_chars(context),
                result_count=len(findings) + len(recommendations),
            )

        return run_bounded(tool_name, _run)

    _handler.__name__ = tool_name
    _handler.__doc__ = description
    server.add_tool(_handler, name=tool_name, structured_output=True)


def register_pack_architecture(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    _register_pack_tool(
        server,
        context,
        tool_name="repository_architecture",
        pack="architecture",
        description="Architecture intelligence posture, findings, and recommendations.",
    )


def register_pack_security(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    _register_pack_tool(
        server,
        context,
        tool_name="repository_security",
        pack="security",
        description="Security intelligence posture, findings, and recommendations.",
    )


def register_pack_dependencies(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    _register_pack_tool(
        server,
        context,
        tool_name="repository_dependencies",
        pack="dependencies",
        description="Dependency intelligence posture, findings, and recommendations.",
    )


def register_pack_tests(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    _register_pack_tool(
        server,
        context,
        tool_name="repository_tests",
        pack="tests",
        description="Test intelligence posture, findings, and recommendations.",
    )


def register_pack_cloud(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    _register_pack_tool(
        server,
        context,
        tool_name="repository_cloud",
        pack="cloud",
        description="Cloud intelligence posture, findings, and recommendations.",
    )


def register_pack_ai_readiness(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    _register_pack_tool(
        server,
        context,
        tool_name="repository_ai_readiness",
        pack="ai_readiness",
        description="AI readiness posture, findings, and recommendations.",
    )


def register_pack_performance(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    _register_pack_tool(
        server,
        context,
        tool_name="repository_performance",
        pack="performance",
        description="Performance intelligence posture, findings, and recommendations.",
    )


def register_repository_health(
    server: FastMCP, context: RepositoryIntelligenceContext
) -> None:
    @server.tool(name="repository_health", structured_output=True)
    def repository_health() -> dict[str, Any]:
        """Bounded MCP and dependency health (no secrets or connection strings)."""

        def _run() -> dict[str, Any]:
            settings = context.settings
            retrieval_enabled = bool(
                settings and settings.knowledge.retrieval.enabled and context.retriever
            )
            answering_enabled = bool(
                settings
                and settings.knowledge.answering.enabled
                and context.answer_engine
            )
            vector_healthy: bool | None = None
            vector_message = None
            if context.vector_store is not None:
                try:
                    store_health = context.vector_store.health()
                    vector_healthy = store_health.healthy
                    vector_message = store_health.message
                except Exception as exc:  # noqa: BLE001
                    vector_healthy = False
                    vector_message = sanitize_exception_message(str(exc))
            embedding_identity: dict[str, Any] = {}
            embedding_mode = "unknown"
            if context.settings is not None:
                embedding_mode = (
                    "deterministic"
                    if context.settings.ai.embedding_provider.startswith("deterministic")
                    else "production"
                )
            if context.embedding_provider is not None:
                try:
                    identity = context.embedding_provider.model_identity()
                    embedding_identity = {
                        "provider_id": getattr(identity, "provider_id", None)
                        or getattr(identity, "provider", None),
                        "model": getattr(identity, "model", None),
                        "model_version": getattr(identity, "model_version", None),
                        "dimension": getattr(identity, "dimension", None),
                        "mode": embedding_mode,
                        "selected": (
                            context.settings.ai.embedding_provider
                            if context.settings is not None
                            else None
                        ),
                        "is_production_model": embedding_mode == "production",
                    }
                    try:
                        emb_health = context.embedding_provider.health()
                        embedding_identity["healthy"] = emb_health.healthy
                        embedding_identity["health_message"] = emb_health.message
                    except Exception as exc:  # noqa: BLE001
                        embedding_identity["healthy"] = False
                        embedding_identity["health_message"] = (
                            sanitize_exception_message(str(exc))
                        )
                except Exception:  # noqa: BLE001
                    embedding_identity = {"available": True, "mode": embedding_mode}
            answer_identity: dict[str, Any] = {}
            answer_mode = "unknown"
            if context.settings is not None:
                answer_mode = (
                    "deterministic"
                    if context.settings.ai.answer_provider.startswith("deterministic")
                    else "production"
                )
            if context.answer_provider is not None:
                answer_identity = context.answer_provider.model_identity().model_dump(
                    mode="json"
                )
                answer_identity["mode"] = answer_mode
                answer_identity["selected"] = (
                    context.settings.ai.answer_provider
                    if context.settings is not None
                    else None
                )
                try:
                    ans_health = context.answer_provider.health()
                    answer_identity["healthy"] = ans_health.healthy
                    answer_identity["health_message"] = ans_health.message
                except Exception as exc:  # noqa: BLE001
                    answer_identity["healthy"] = False
                    answer_identity["health_message"] = sanitize_exception_message(
                        str(exc)
                    )
            enabled: list[str] = []
            disabled: list[str] = []
            for name in ("retrieval", "answering", "vector_store"):
                if name == "retrieval" and retrieval_enabled:
                    enabled.append(name)
                elif name == "answering" and answering_enabled:
                    enabled.append(name)
                elif name == "vector_store" and context.vector_store is not None:
                    enabled.append(name)
                else:
                    disabled.append(name)
            for tool_name in sorted(
                k
                for k, v in context.tools.model_dump().items()
                if isinstance(v, bool)
            ):
                if getattr(context.tools, tool_name):
                    enabled.append(f"tool:{tool_name}")
                else:
                    disabled.append(f"tool:{tool_name}")
            version = context.mcp.server_version or PACKAGE_VERSION
            diagnostics = [
                McpDiagnostic(
                    code=item.get("code", "composition"),
                    message=str(item.get("message", "")),
                    severity=str(item.get("severity", "info")),
                )
                for item in context.composition_diagnostics
                if item.get("message")
            ]
            if vector_message:
                diagnostics.append(
                    McpDiagnostic(
                        code="vector_store_health",
                        message=vector_message,
                        severity="info" if vector_healthy else "warning",
                    )
                )
            status = McpToolStatus.SUCCESS
            if context.composition_diagnostics:
                status = McpToolStatus.PARTIAL
            if vector_healthy is False:
                status = McpToolStatus.FAILED
            fingerprint = fingerprint_payload(
                {
                    "server": context.mcp.server_name,
                    "version": version,
                    "transport": context.mcp.transport,
                    "provider": context.vector_store_provider,
                    "retrieval": retrieval_enabled,
                    "answering": answering_enabled,
                }
            )
            health_response = McpHealthResponse(
                status=status,
                server_name=context.mcp.server_name,
                server_version=version,
                transport=context.mcp.transport,
                retrieval_available=retrieval_enabled,
                answering_available=answering_enabled,
                vector_store_provider=context.vector_store_provider,
                vector_store_healthy=vector_healthy,
                vector_store_persistent=context.vector_store_persistent,
                embedding_provider=embedding_identity,
                answer_provider=answer_identity,
                enabled_capabilities=tuple(sorted(set(enabled))),
                disabled_capabilities=tuple(sorted(set(disabled))),
                diagnostics=tuple(diagnostics),
                fingerprint=fingerprint,
            )
            payload = to_mcp_payload(health_response)
            assert isinstance(payload, dict)
            return payload

        return run_bounded("repository_health", _run)
