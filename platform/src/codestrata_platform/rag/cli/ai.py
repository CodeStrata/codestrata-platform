"""CLI for AI provider configuration and health (Phase 5.8)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from codestrata.ai.providers.registry import get_default_registry
from codestrata.config import load_settings
from codestrata.security.database_url import sanitize_exception_message
from codestrata_platform.rag.application.answering.factory import (
    create_answer_provider,
    resolve_answer_provider_name,
)
from codestrata_platform.rag.embedding.factory import (
    create_embedding_provider,
    resolve_embedding_provider_name,
)

ai_app = typer.Typer(
    name="ai",
    help=(
        "CodeStrata Platform — AI provider utilities (optional capability).\n\n"
        "Embeddings and grounded-answer provider health/config helpers. "
        "AI is not part of the product name. Community assess can use "
        "optional --with-ai without these Platform commands."
    ),
    no_args_is_help=True,
)


def _load_or_exit(config: Path) -> Any:
    try:
        return load_settings(config)
    except (FileNotFoundError, ValueError, OSError) as error:
        typer.echo(f"Failed to load configuration: {error}", err=True)
        raise typer.Exit(code=1) from error


def _provider_mode(name: str) -> str:
    return "deterministic" if name.startswith("deterministic") else "production"


@ai_app.command("providers")
def providers_cmd() -> None:
    """List registered embedding and answer providers."""

    registry = get_default_registry()
    payload = {
        "embedding_providers": list(registry.list_embedding_providers()),
        "answer_providers": list(registry.list_answer_providers()),
        "notes": (
            "Select independently via [ai].embedding_provider and "
            "[ai].answer_provider. No silent fallback between providers."
        ),
    }
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@ai_app.command("config")
def config_cmd(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to codestrata.toml."),
    ] = Path("codestrata.toml"),
) -> None:
    """Show selected AI provider configuration (no secrets)."""

    settings = _load_or_exit(config)
    emb_name = resolve_embedding_provider_name(settings=settings)
    ans_name = resolve_answer_provider_name(settings=settings)
    bed = settings.ai.bedrock
    oai = settings.ai.openai
    payload = {
        "embedding_provider": emb_name,
        "answer_provider": ans_name,
        "embedding_mode": _provider_mode(emb_name),
        "answer_mode": _provider_mode(ans_name),
        "assessment_provider": settings.ai.provider,
        "bedrock": {
            "region": bed.region,
            "embedding_model": bed.embedding_model,
            "answer_model": bed.answer_model or bed.model_id,
            "timeout_seconds": bed.timeout_seconds,
            "max_retries": bed.max_retries,
        },
        "openai": {
            "api_key_env": oai.api_key_env,
            "base_url": oai.base_url or None,
            "embedding_model": oai.embedding_model,
            "answer_model": oai.answer_model,
            "embedding_dimensions": oai.embedding_dimensions or None,
            "timeout_seconds": oai.timeout_seconds,
            "max_retries": oai.max_retries,
        },
        "knowledge_gates": {
            "embedding_enabled": settings.knowledge.embedding.enabled,
            "indexing_enabled": settings.knowledge.indexing.enabled,
            "retrieval_enabled": settings.knowledge.retrieval.enabled,
            "answering_enabled": settings.knowledge.answering.enabled,
        },
    }
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@ai_app.command("health")
def health_cmd(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to codestrata.toml."),
    ] = Path("codestrata.toml"),
    live: Annotated[
        bool,
        typer.Option(
            "--live",
            help="Construct providers and call health() (may contact APIs).",
        ),
    ] = False,
) -> None:
    """Report AI provider configuration health (sanitized)."""

    settings = _load_or_exit(config)
    emb_name = resolve_embedding_provider_name(settings=settings)
    ans_name = resolve_answer_provider_name(settings=settings)
    payload: dict[str, Any] = {
        "embedding_provider": emb_name,
        "answer_provider": ans_name,
        "embedding_mode": _provider_mode(emb_name),
        "answer_mode": _provider_mode(ans_name),
        "live": live,
        "embedding": {"configured": True},
        "answer": {"configured": True},
    }
    if not live:
        payload["message"] = (
            "Configuration parsed successfully. Pass --live to construct "
            "providers and probe health (requires credentials for production)."
        )
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    try:
        embedder = create_embedding_provider(
            settings.knowledge.embedding,
            codestrata_settings=settings,
        )
        health = embedder.health()
        identity = embedder.model_identity()
        payload["embedding"] = {
            "healthy": health.healthy,
            "message": health.message,
            "provider_id": identity.provider_id,
            "model": identity.model,
            "dimension": identity.dimension,
            "detail": health.detail,
        }
    except Exception as exc:  # noqa: BLE001
        payload["embedding"] = {
            "healthy": False,
            "message": sanitize_exception_message(str(exc)),
        }

    try:
        answer = create_answer_provider(
            settings.knowledge.answering,
            codestrata_settings=settings,
        )
        answer_health = answer.health()
        answer_identity = answer.model_identity()
        payload["answer"] = {
            "healthy": answer_health.healthy,
            "message": answer_health.message,
            "provider_id": answer_identity.provider_id,
            "model": answer_identity.model,
            "detail": answer_health.detail,
        }
    except Exception as exc:  # noqa: BLE001
        payload["answer"] = {
            "healthy": False,
            "message": sanitize_exception_message(str(exc)),
        }

    typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    emb_ok = payload.get("embedding", {}).get("healthy", False)
    ans_ok = payload.get("answer", {}).get("healthy", False)
    if not (emb_ok and ans_ok):
        raise typer.Exit(code=1)


__all__ = ["ai_app"]
