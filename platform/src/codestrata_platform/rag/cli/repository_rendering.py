"""Human-readable and JSON rendering for repository grounded-answer CLI."""

from __future__ import annotations

import json
from typing import Any

import typer

from codestrata_platform.rag.domain.answering import GroundedAnswerResult

EXIT_ERROR = 1


def result_to_dict(
    result: GroundedAnswerResult,
    *,
    repository_id: str,
    question: str,
    tenant_id: str,
    scan_id: str | None,
) -> dict[str, Any]:
    """Build a stable CLI JSON payload from a grounded answer result."""

    answer = result.answer
    payload: dict[str, Any] = {
        "repository_id": repository_id,
        "tenant_id": tenant_id,
        "scan_id": scan_id,
        "question": question,
        "status": result.status.value,
        "summary": answer.summary if answer else None,
        "confidence": answer.confidence.value if answer else None,
        "statements": (
            [item.model_dump(mode="json") for item in answer.statements] if answer else []
        ),
        "citations": (
            [item.model_dump(mode="json") for item in answer.citations] if answer else []
        ),
        "coverage": result.coverage.model_dump(mode="json"),
        "limitations": [item.message for item in result.limitations],
    }
    if result.diagnostics:
        payload["diagnostics"] = [item.model_dump(mode="json") for item in result.diagnostics]
    return payload


def dumps_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def emit_answer_result(
    result: GroundedAnswerResult,
    *,
    repository_id: str,
    question: str,
    tenant_id: str,
    scan_id: str | None,
    as_json: bool,
) -> None:
    """Print JSON or a concise human summary."""

    payload = result_to_dict(
        result,
        repository_id=repository_id,
        question=question,
        tenant_id=tenant_id,
        scan_id=scan_id,
    )
    if as_json:
        typer.echo(dumps_json(payload))
        return

    answer = result.answer
    typer.echo(f"Status: {result.status.value}")
    if answer is not None and answer.summary:
        typer.echo(f"Summary: {answer.summary}")
    if answer is not None and answer.confidence is not None:
        typer.echo(f"Confidence: {answer.confidence.value}")

    statements = payload["statements"]
    if statements:
        typer.echo("Statements:")
        for item in statements:
            labels = ", ".join(item.get("citation_labels") or ())
            text = item.get("text") or ""
            typer.echo(f"  - {text}")
            if labels:
                typer.echo(f"    citations: {labels}")

    citations = payload["citations"]
    if citations:
        typer.echo("Citations:")
        for item in citations:
            label = item.get("citation_label") or "?"
            source = item.get("source_type") or "unknown"
            path = item.get("file_path")
            location = f"{source}" + (f" ({path})" if path else "")
            typer.echo(f"  - {label}: {location}")

    if result.limitations:
        typer.echo("Limitations:")
        for item in result.limitations:
            typer.echo(f"  - {item.message}")
