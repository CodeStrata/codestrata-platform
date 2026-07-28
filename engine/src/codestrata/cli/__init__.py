"""Command-line interface for CodeStrata."""

from pathlib import Path
from typing import Annotated

import typer

from codestrata.cli.acceptance import acceptance_app
from codestrata.cli.agent import agent_app
from codestrata.cli.architecture import architecture_app
from codestrata.cli.assess import (
    DEFAULT_ASSESS_MAX_OUTPUT_TOKENS,
    DEFAULT_ASSESS_OUTPUT_DIRECTORY,
    DEFAULT_ASSESS_REPORT_TITLE,
    DEFAULT_ASSESS_TEMPERATURE,
    AssessmentApplicationService,
    AssessmentCommandError,
    AssessmentCommandResult,
    register_assess_command,
    run_assessment,
)
from codestrata.cli.config_cmd import config_app
from codestrata.cli.doctor import register_doctor_command
from codestrata.cli.evidence import evidence_app
from codestrata.cli.examples_cmd import register_examples_command
from codestrata.cli.incremental import incremental_app
from codestrata.cli.init_cmd import register_init_command
from codestrata.cli.onboard import register_onboard_command
from codestrata.cli.release import release_app
from codestrata.cli.report import report_app
from codestrata.cli.roadmap import roadmap_app
from codestrata.cli.rules import rules_app
from codestrata.config import load_settings
from codestrata.extensions import load_cli_extensions
from codestrata.extensions.cli_cmd import register_extensions_command
from codestrata.logging_config import configure_logging
from codestrata.output_format import OutputFormat
from codestrata.package_metadata import (
    format_about,
    format_version_details,
    format_version_line,
)
from codestrata.reporters import (
    ConsoleReporter,
    HtmlFileReporter,
    JsonFileReporter,
    TextFileReporter,
    create_report_paths,
    retain_recent_reports,
)
from codestrata.reporting import AssessmentMode
from codestrata.repository_auth.exceptions import RepositoryAccessError
from codestrata.result_renderer import render_json
from codestrata.services.default_pipeline import create_default_analysis_service
from codestrata.services.scan_comparison_service import ScanComparisonService
from codestrata.services.scanners.github_repository_scanner import (
    GitHubRepositoryScanner,
)
from codestrata.static_analysis.exceptions import StaticAnalysisProviderError

_METADATA_SUBCOMMANDS = frozenset({"version", "about", "examples", "extensions"})

app = typer.Typer(
    name="codestrata",
    help=(
        "CodeStrata Engine (Community Edition) — scan repositories and generate "
        "deterministic Engineering Assessment reports.\n\n"
        "Community golden path (no Platform required):\n"
        "  codestrata init\n"
        "  codestrata doctor\n"
        "  codestrata assess --repo . --output reports --no-ai\n\n"
        "Optional AI advisor (your own supported provider):\n"
        "  codestrata assess --repo . --output reports --with-ai\n\n"
        "Exit codes: 0 success · 1 failure · 2 invalid usage.\n"
        "AI unavailable with --with-ai still exits 0 when reports are written "
        "(enhancements skipped).\n\n"
        "Primary workflow: assess (HTML + JSON Engineering Assessment).\n"
        "Legacy/advanced: scan (clone+analyze; prefer assess).\n"
        "Platform groups appear only when Platform is installed; Community "
        "does not require them.\n\n"
        "Docs: docs/README.md (portal) · docs/quick-start.md · "
        "docs/troubleshooting.md"
    ),
    no_args_is_help=True,
)


def _eager_version_option(value: bool) -> None:
    """Print the short version line and exit when ``--version`` is passed."""

    if not value:
        return
    typer.echo(format_version_line())
    raise typer.Exit(0)


@app.callback()
def _root_callback(
    ctx: typer.Context,
    show_version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            help="Show the CodeStrata version and exit.",
            callback=_eager_version_option,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Configure logging for runtime commands; skip for metadata commands."""

    del show_version
    if ctx.invoked_subcommand in _METADATA_SUBCOMMANDS:
        return
    configure_logging()


@app.command("version", rich_help_panel="Primary")
def version_command() -> None:
    """Display the CodeStrata version and runtime environment."""

    typer.echo(format_version_details())


@app.command(rich_help_panel="Primary")
def about() -> None:
    """Display CodeStrata product and project information."""

    typer.echo(format_about())


@app.command(rich_help_panel="Advanced")
def scan(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to the CodeStrata TOML configuration file.",
        ),
    ] = Path("codestrata.toml"),
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format.",
            case_sensitive=False,
        ),
    ] = OutputFormat.TEXT,
    report_directory: Annotated[
        Path,
        typer.Option(
            "--report-directory",
            help="Directory where analysis reports are written.",
        ),
    ] = Path("reports"),
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Display the complete report in the terminal.",
        ),
    ] = False,
) -> None:
    """[Legacy/advanced] Clone and analyze a GitHub repository from codestrata.toml.

    Prefer the primary workflow:

        codestrata assess --repo <path-or-url> --output reports --no-ai

    ``scan`` requires ``[repository].url`` and writes text/json/html via the
    older analysis reporters.
    """

    try:
        settings = load_settings(config)
    except (FileNotFoundError, ValueError, OSError) as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error

    if not settings.repository.url:
        typer.secho(
            "codestrata scan requires [repository].url in the configuration file.\n\n"
            "Fix: set a GitHub URL in codestrata.toml, for example:\n"
            "  [repository]\n"
            '  url = "https://github.com/YOUR_ORG/YOUR_REPO"\n'
            '  branch = "main"\n\n'
            "For a local checkout, use:\n"
            "  codestrata assess --repo /path/to/repo --output reports",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    scanner = GitHubRepositoryScanner(
        workspace_directory=settings.workspace.directory,
        branch=settings.repository.branch,
        clean_before_clone=settings.workspace.clean_before_clone,
        authentication=settings.repository.authentication,
    )

    try:
        repository = scanner.scan(settings.repository.url)
    except RepositoryAccessError as error:
        typer.secho(
            f"{error}\n\n"
            "Fix: verify the repository URL, network access, and authentication "
            "(CODESTRATA_GITHUB_TOKEN or SSH agent). See docs/troubleshooting.md.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1) from error

    analysis_service = create_default_analysis_service(settings)

    try:
        result = analysis_service.analyze(repository)
    except StaticAnalysisProviderError as exc:
        typer.secho(f"Static analysis failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    report_paths = create_report_paths(
        result=result,
        base_directory=report_directory,
    )

    comparison = ScanComparisonService().compare(
        current=result,
        repository_directory=report_paths.directory.parent,
        current_run_directory=report_paths.directory,
        current_timestamp=report_paths.timestamp,
    )
    result = result.model_copy(update={"comparison": comparison})

    TextFileReporter().write(
        result=result,
        output_path=report_paths.text_report,
    )

    JsonFileReporter().write(
        result=result,
        output_path=report_paths.json_report,
    )

    HtmlFileReporter().write(
        result=result,
        output_path=report_paths.html_report,
    )

    retain_recent_reports(report_paths.directory.parent)

    if output == OutputFormat.JSON:
        render_json(result)
        return

    console_reporter = ConsoleReporter()

    if verbose:
        console_reporter.render_detailed(result)
        return

    console_reporter.render_summary(
        result=result,
        text_report_path=report_paths.text_report,
        json_report_path=report_paths.json_report,
        html_report_path=report_paths.html_report,
    )


def _register_mcp_group(root: typer.Typer) -> None:
    """Register MCP commands when the optional ``mcp`` extra is installed."""

    try:
        import mcp  # noqa: F401
    except ImportError:
        mcp_stub = typer.Typer(
            name="mcp",
            help="MCP commands require the optional mcp extra.",
            # False so bare `codestrata mcp` prints the install hint below.
            no_args_is_help=False,
        )

        @mcp_stub.callback(invoke_without_command=True)
        def _mcp_missing() -> None:
            typer.echo(
                "CodeStrata MCP is unavailable. Install the optional extra:\n"
                "  pip install 'codestrata[mcp]'",
                err=True,
            )
            raise typer.Exit(code=1)

        root.add_typer(mcp_stub, name="mcp", rich_help_panel="Advanced")
        return

    from codestrata.cli.mcp import mcp_app

    root.add_typer(mcp_app, name="mcp", rich_help_panel="Advanced")


def _register_platform_cli_extensions(root: typer.Typer) -> None:
    """Attach Platform CLI groups via entry points; stub when absent."""

    loaded = load_cli_extensions()
    if loaded:
        for register in loaded:
            register(root)
        return

    for name, help_text, message in (
        (
            "enterprise",
            "CodeStrata Platform Engineering Knowledge Graph (not in Community Engine).",
            "Engineering Knowledge Graph is a CodeStrata Platform capability and is "
            "not included in the Community Engine.\n"
            "Install codestrata-platform in private deployments to enable it.",
        ),
        (
            "repository",
            "CodeStrata Platform repository RAG (not in Community Engine).",
            "Repository RAG commands are a CodeStrata Platform capability and "
            "are not included in the Community Engine.\n"
            "Install codestrata-platform in private deployments to enable them.",
        ),
        (
            "ai",
            "CodeStrata Platform AI provider commands (not in Community Engine).",
            "AI embedding/answer provider commands are a CodeStrata Platform "
            "capability and are not included in the Community Engine.\n"
            "Install codestrata-platform in private deployments to enable them.\n"
            "Community assess still supports optional [ai] settings with --with-ai.",
        ),
    ):
        stub = typer.Typer(name=name, help=help_text, no_args_is_help=False)

        def _missing(msg: str = message) -> None:
            typer.echo(msg, err=True)
            raise typer.Exit(code=1)

        stub.callback(invoke_without_command=True)(_missing)
        root.add_typer(stub, name=name, rich_help_panel="Platform")


register_assess_command(app)
register_init_command(app)
register_doctor_command(app)
register_examples_command(app)
register_extensions_command(app)
register_onboard_command(app)
_register_mcp_group(app)
app.add_typer(config_app, name="config", rich_help_panel="Configuration")
app.add_typer(agent_app, name="agent", rich_help_panel="Advanced")
app.add_typer(incremental_app, name="incremental", rich_help_panel="Advanced")
_register_platform_cli_extensions(app)
app.add_typer(rules_app, name="rules", rich_help_panel="Advanced")
app.add_typer(evidence_app, name="evidence", rich_help_panel="Advanced")
app.add_typer(architecture_app, name="architecture", rich_help_panel="Advanced")
app.add_typer(roadmap_app, name="roadmap", rich_help_panel="Advanced")
app.add_typer(report_app, name="report", rich_help_panel="Advanced")
app.add_typer(acceptance_app, name="acceptance", rich_help_panel="Maintainer")
app.add_typer(release_app, name="release", rich_help_panel="Maintainer")

__all__ = [
    "DEFAULT_ASSESS_MAX_OUTPUT_TOKENS",
    "DEFAULT_ASSESS_OUTPUT_DIRECTORY",
    "DEFAULT_ASSESS_REPORT_TITLE",
    "DEFAULT_ASSESS_TEMPERATURE",
    "AssessmentApplicationService",
    "AssessmentCommandError",
    "AssessmentCommandResult",
    "AssessmentMode",
    "about",
    "app",
    "run_assessment",
    "scan",
    "version_command",
]


if __name__ == "__main__":
    app()
