"""CLI adapter for repository onboarding (Phase 5.11)."""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Annotated

import typer

from aimf.application.assessment import DEFAULT_ASSESS_OUTPUT_DIRECTORY
from aimf.application.onboarding import (
    OnboardingApplicationService,
    format_onboarding_result,
    run_onboarding,
)
from aimf.domain.onboarding.errors import OnboardingError
from aimf.logging_config import configure_logging


def register_onboard_command(app: typer.Typer) -> None:
    """Register ``aimf onboard`` on the root Typer application."""

    @app.command("onboard")
    def onboard(
        repository: Annotated[
            str,
            typer.Argument(
                help="Local repository path or GitHub URL to onboard.",
            ),
        ],
        config: Annotated[
            Path,
            typer.Option(
                "--config",
                "-c",
                help="Path to aimf.toml configuration.",
            ),
        ] = Path("aimf.toml"),
        output: Annotated[
            Path,
            typer.Option(
                "--output",
                "-o",
                help="Directory for assessment reports and onboarding manifests.",
            ),
        ] = DEFAULT_ASSESS_OUTPUT_DIRECTORY,
        force_reindex: Annotated[
            bool,
            typer.Option(
                "--force-reindex",
                help="Clear prior vector-store scope for this repository before indexing.",
            ),
        ] = False,
        skip_report: Annotated[
            bool,
            typer.Option(
                "--skip-report",
                help="Run assessment and knowledge steps without writing HTML/JSON reports.",
            ),
        ] = False,
        skip_index: Annotated[
            bool,
            typer.Option(
                "--skip-index",
                help="Skip knowledge projection, embedding, and indexing.",
            ),
        ] = False,
        provider: Annotated[
            str | None,
            typer.Option(
                "--provider",
                help="Embedding provider override: deterministic, bedrock, or openai.",
            ),
        ] = None,
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Enable diagnostic logging and stack traces on failure.",
            ),
        ] = False,
    ) -> None:
        """Onboard a repository into a queryable CodeStrata knowledge base.

        Orchestrates existing assessment, knowledge, and reporting services:

            aimf onboard ./my-repo --config aimf.toml --output reports
        """

        configure_logging(level="DEBUG" if verbose else "WARNING")
        try:
            result = run_onboarding(
                repository,
                config_path=config,
                output_directory=output,
                force_reindex=force_reindex,
                skip_report=skip_report,
                skip_index=skip_index,
                provider=provider,
            )
        except OnboardingError as error:
            typer.secho(str(error), fg=typer.colors.RED, err=True)
            if verbose:
                traceback.print_exc()
            raise typer.Exit(code=1) from error
        except Exception as error:  # noqa: BLE001 - CLI boundary
            typer.secho(
                f"Onboarding failed: {error}\n\n"
                "Fix: re-run with --verbose for details.",
                fg=typer.colors.RED,
                err=True,
            )
            if verbose:
                traceback.print_exc()
            raise typer.Exit(code=1) from error

        typer.echo(format_onboarding_result(result))


__all__ = [
    "OnboardingApplicationService",
    "register_onboard_command",
    "run_onboarding",
]
