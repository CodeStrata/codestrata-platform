"""CLI for anonymous Community telemetry preference and status commands.

``codestrata telemetry status`` reports the privacy-first runtime posture
(side-effect-free). ``codestrata telemetry preview`` shows an illustrative
privacy-safe event (local only; no transmission). Legacy preference controls
(enable/disable/reset/show) remain available separately and do not authorize
the privacy-first runtime.
"""

from __future__ import annotations

import json
from typing import Annotated

import typer

from codestrata.telemetry.constants import EventName
from codestrata.telemetry.preview_builder import build_privacy_first_telemetry_preview
from codestrata.telemetry.preview_formatting import format_privacy_first_telemetry_preview
from codestrata.telemetry.preview_policy import PreviewPolicyError
from codestrata.telemetry.service import get_legacy_telemetry_service
from codestrata.telemetry.status import build_privacy_first_telemetry_status
from codestrata.telemetry.status_formatting import format_privacy_first_telemetry_status

telemetry_app = typer.Typer(
    name="telemetry",
    help=(
        "Anonymous Community telemetry (disabled by default).\n\n"
        "Examples:\n"
        "  codestrata telemetry status\n"
        "  codestrata telemetry preview\n"
        "  codestrata telemetry enable\n"
        "  codestrata telemetry disable\n"
        "  codestrata telemetry reset\n"
        "  codestrata telemetry show\n\n"
        "``status`` and ``preview`` are privacy-first runtime transparency "
        "commands. Legacy preference commands manage separate local opt-in "
        "state and do not authorize the privacy-first runtime for normal "
        "assess/report commands.\n\n"
        "Never collects source code, repository names, findings, prompts, or "
        "credentials. See PRIVACY.md and https://docs.codestrata.ai/security/privacy"
    ),
    no_args_is_help=True,
)


def _echo_json(payload: object) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@telemetry_app.command("status")
def telemetry_status() -> None:
    """Show privacy-first telemetry posture (no side effects).

    Does not read preferences, installation identity, queues, or endpoints.
    Does not prompt, transmit, or mutate files.
    """

    status = build_privacy_first_telemetry_status()
    typer.echo(format_privacy_first_telemetry_status(status), nl=False)


@telemetry_app.command("preview")
def telemetry_preview(
    event: Annotated[
        str | None,
        typer.Option(
            "--event",
            help=(
                "Runtime event to preview "
                "(application_started, application_completed, feature_invoked, "
                "feature_completed, operation_failed). Default: feature_invoked."
            ),
        ),
    ] = None,
) -> None:
    """Show an illustrative privacy-safe telemetry event (local only).

    Displays exactly what the privacy-first runtime would pass to a future
    transport. Uses fixed illustrative categorical values. Does not transmit,
    save consent, use installation identity, or inspect repositories.
    """

    try:
        preview = build_privacy_first_telemetry_preview(event_name=event)
    except PreviewPolicyError as error:
        typer.echo(f"Invalid preview: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(format_privacy_first_telemetry_preview(preview), nl=False)


@telemetry_app.command("enable")
def telemetry_enable() -> None:
    """Enable legacy anonymous telemetry preference (does not enable runtime)."""

    status = get_legacy_telemetry_service().enable(emit_events=False)
    typer.echo("Legacy anonymous telemetry preference enabled.")
    typer.echo(
        "Note: the privacy-first runtime remains disabled for normal CLI "
        "commands. Process-local assess consent flags do not persist; "
        "see `codestrata telemetry status`."
    )
    _echo_json(status)


@telemetry_app.command("disable")
def telemetry_disable() -> None:
    """Disable anonymous telemetry preference (legacy compatibility only)."""

    status = get_legacy_telemetry_service().disable(emit_events=False)
    typer.echo("Legacy anonymous telemetry preference disabled.")
    _echo_json(status)


@telemetry_app.command("reset")
def telemetry_reset() -> None:
    """Reset installation id, preferences, and local queue (legacy only)."""

    status = get_legacy_telemetry_service().reset()
    typer.echo(
        "Legacy telemetry identity and preferences reset. "
        "Legacy preference telemetry is disabled."
    )
    _echo_json(status)


@telemetry_app.command("show")
def telemetry_show(
    event: Annotated[
        str,
        typer.Option(
            "--event",
            help="Event name to preview (default: assessment_completed).",
        ),
    ] = EventName.ASSESSMENT_COMPLETED.value,
) -> None:
    """Display a sample legacy payload shape (does not transmit via product runtime)."""

    try:
        payload = get_legacy_telemetry_service().show_sample_payload(event=event)
    except ValueError as error:
        typer.echo(f"Invalid event: {error}", err=True)
        raise typer.Exit(code=2) from error
    _echo_json(payload)


def register_telemetry_command(app: typer.Typer) -> None:
    """Register the ``telemetry`` command group."""

    app.add_typer(telemetry_app, name="telemetry", rich_help_panel="Configuration")
