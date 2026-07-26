"""CLI for report contract validation (Phase 5.12)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from codestrata.application.report_validation import (
    validate_report_json,
    validation_result_payload,
)

report_app = typer.Typer(
    name="report",
    help=(
        "Report contract helpers (Phase 5.12).\n\n"
        "Validate report.json schema, references, duplicates, evidence links, "
        "and roadmap traceability without re-running assessment."
    ),
    no_args_is_help=True,
)


@report_app.command("validate")
def validate_report(
    report: Annotated[
        Path,
        typer.Argument(help="Path to report.json from an assess/onboard run."),
    ],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Validate a CodeStrata report.json against the hardened report contract."""

    result = validate_report_json(report)
    payload = validation_result_payload(result)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = "PASS" if result.ok else "FAIL"
        typer.echo(f"report validation: {status}")
        typer.echo(f"schema_version: {result.schema_version}")
        typer.echo(
            f"issues: {payload['issue_count']} "
            f"(errors={payload['error_count']}, warnings={payload['warning_count']})"
        )
        for item in result.issues:
            typer.echo(f"  [{item.severity}] {item.code} @ {item.path}: {item.message}")
    if not result.ok:
        raise typer.Exit(code=1)
