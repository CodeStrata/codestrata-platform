"""Thin Typer adapter for repository grounded answering.

Delegates to GroundedAnswerEngine via the same composition path as MCP
``repository_answer``. No assessment, retrieval, or answering business logic here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from codestrata.application.knowledge.queries import (
    KnowledgeQueryService,
    RepositoryQueryNotFoundError,
)
from codestrata.config import CodestrataSettings, load_settings
from codestrata.security.database_url import sanitize_exception_message
from codestrata_platform.rag.application.answering import GroundedAnswerEngine
from codestrata_platform.rag.cli.repository_rendering import EXIT_ERROR, emit_answer_result
from codestrata_platform.rag.domain.answering import AnswerStyle, GroundedAnswerRequest
from codestrata_platform.rag.mcp.repository_common import (
    build_filters,
    build_scope,
    resolve_latest_run_id,
)

repository_app = typer.Typer(
    name="repository",
    help=(
        "Repository knowledge commands (grounded search and answering).\n\n"
        "Uses indexed repository knowledge; requires retrieval and answering gates."
    ),
    no_args_is_help=True,
)


def _load_settings_or_exit(config: Path) -> CodestrataSettings:
    try:
        return load_settings(config)
    except (FileNotFoundError, ValueError, OSError) as error:
        typer.secho(f"Configuration error: {error}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=EXIT_ERROR) from error


def _compose_answer_engine(
    settings: CodestrataSettings,
) -> tuple[GroundedAnswerEngine | None, KnowledgeQueryService]:
    """Return (GroundedAnswerEngine | None, KnowledgeQueryService)."""

    from codestrata.infrastructure.knowledge_store import create_knowledge_query_service
    from codestrata_platform.rag.mcp.composition import compose_repository_intelligence

    queries = create_knowledge_query_service(settings=settings)
    context = compose_repository_intelligence(queries=queries, settings=settings)
    return context.answer_engine, queries


@repository_app.command("answer")
def answer_command(
    repository: Annotated[
        str,
        typer.Argument(help="Repository ID, canonical key, or GitHub URL."),
    ],
    question: Annotated[
        str,
        typer.Argument(help="Natural-language question over indexed knowledge."),
    ],
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to codestrata.toml."),
    ] = Path("codestrata.toml"),
    tenant_id: Annotated[
        str,
        typer.Option(
            "--tenant-id",
            help="Tenant scope for retrieval (must match indexed knowledge).",
        ),
    ] = "default",
    scan_id: Annotated[
        str | None,
        typer.Option(
            "--scan-id",
            help="Optional assessment run / scan scope (defaults to latest completed run).",
        ),
    ] = None,
    answer_style: Annotated[
        str,
        typer.Option(
            "--answer-style",
            help=(
                "Answer style: concise, detailed, findings_summary, "
                "recommendation_summary, architecture_explanation, evidence_only."
            ),
        ),
    ] = "concise",
    top_k: Annotated[
        int,
        typer.Option("--top-k", help="Maximum retrieval hits to consider.", min=1),
    ] = 10,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON."),
    ] = False,
) -> None:
    """Answer a repository question using citation-bound grounded evidence."""

    settings = _load_settings_or_exit(config)
    if not settings.knowledge.answering.enabled:
        typer.secho(
            "Grounded answering is disabled (knowledge.answering.enabled=false).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=EXIT_ERROR)
    if not settings.knowledge.retrieval.enabled:
        typer.secho(
            "Knowledge retrieval is disabled (knowledge.retrieval.enabled=false).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=EXIT_ERROR)

    engine, queries = _compose_answer_engine(settings)
    if engine is None:
        typer.secho(
            "Grounded answer engine is unavailable. Check knowledge provider "
            "configuration and vector store connectivity.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=EXIT_ERROR)

    compact_question = question.strip()
    if not compact_question:
        typer.secho("Question must be non-empty.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=EXIT_ERROR)

    try:
        summary = queries.resolve_repository(repository.strip())
    except RepositoryQueryNotFoundError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=EXIT_ERROR) from error

    repository_id = summary.repository_id
    resolved_scan_id = scan_id.strip() if scan_id else None
    if resolved_scan_id is None:
        resolved_scan_id = resolve_latest_run_id(queries, repository_id)

    try:
        style = AnswerStyle(answer_style.strip().lower())
    except ValueError as error:
        typer.secho(
            "answer_style must be one of: concise, detailed, findings_summary, "
            "recommendation_summary, architecture_explanation, evidence_only",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=EXIT_ERROR) from error

    scope = build_scope(
        tenant_id=tenant_id.strip(),
        repository_id=repository_id,
        scan_id=resolved_scan_id,
    )

    try:
        result = engine.answer(
            GroundedAnswerRequest(
                question=compact_question,
                scope=scope,
                filters=build_filters(),
                top_k=top_k,
                style=style,
                include_evidence=False,
                include_retrieval_context=False,
                include_diagnostics=True,
            )
        )
    except Exception as error:  # noqa: BLE001 - CLI boundary
        typer.secho(
            f"Grounded answer failed: {sanitize_exception_message(str(error))}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=EXIT_ERROR) from error

    emit_answer_result(
        result,
        repository_id=repository_id,
        question=compact_question,
        tenant_id=tenant_id.strip(),
        scan_id=resolved_scan_id,
        as_json=json_output,
    )

    if result.status.value in {"failed", "disabled"}:
        raise typer.Exit(code=EXIT_ERROR)
