"""CLI for evidence planning plus specialized language providers."""

from __future__ import annotations

import json
import webbrowser
from pathlib import Path
from typing import Annotated

import typer

from codestrata.application.evidence.framework.service import EvidenceFrameworkService
from codestrata.application.evidence.language.factory import create_language_evidence_service
from codestrata.config import CodestrataSettings, load_settings
from codestrata.domain.evidence.language.capability_catalog import (
    CAP_ARCHITECTURE_LAYERS,
    CAP_ARCHITECTURE_UNITS,
    CAP_DEPENDENCIES_IMPORTS,
    CAP_DEPENDENCIES_TYPE_ONLY,
    CAP_FRAMEWORK_USAGE,
    CAP_SOURCE_FILES,
)
from codestrata.interfaces.evidence_studio import EvidenceStudioServer
from codestrata.security.redaction import redact_secrets

evidence_app = typer.Typer(
    name="evidence",
    help=(
        "Define, preview, collect, normalize, assess, and report repository evidence.\n\n"
        "Start with `codestrata evidence studio --repo .` for the local visual workflow, "
        "or `codestrata evidence init --repo .` for a portable YAML plan. Existing "
        "language-provider commands remain available under `providers`."
    ),
    no_args_is_help=True,
)

providers_app = typer.Typer(
    name="providers",
    help="List and inspect language evidence providers.",
    no_args_is_help=True,
)
evidence_app.add_typer(providers_app, name="providers")


@providers_app.command("list")
def list_providers(
    language: Annotated[
        str | None,
        typer.Option("--language", help="Filter by language (python, java, javascript)."),
    ] = None,
    capability: Annotated[
        str | None,
        typer.Option("--capability", help="Filter by capability ID."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to codestrata.toml."),
    ] = Path("codestrata.toml"),
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
) -> None:
    """List registered language evidence providers."""

    settings = _load_optional_settings(config)
    service = create_language_evidence_service(settings)
    rows = service.list_providers(language=language, capability=capability)
    if json_output:
        typer.echo(json.dumps({"providers": rows}, indent=2, ensure_ascii=False))
        return
    if not rows:
        typer.echo("No providers registered.")
        return
    for row in rows:
        typer.echo(
            f"{row['provider_id']}@{row['provider_version']} "
            f"languages={','.join(row['supported_languages'])}"
        )


@providers_app.command("inspect")
def inspect_provider(
    provider_id: Annotated[str, typer.Argument(help="Provider ID.")],
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to codestrata.toml."),
    ] = Path("codestrata.toml"),
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
) -> None:
    """Inspect one language evidence provider."""

    settings = _load_optional_settings(config)
    service = create_language_evidence_service(settings)
    try:
        row = service.inspect_provider(provider_id)
    except Exception as error:  # noqa: BLE001
        typer.echo(redact_secrets(str(error)), err=True)
        raise typer.Exit(code=1) from error
    if json_output:
        typer.echo(json.dumps(row, indent=2, ensure_ascii=False))
        return
    typer.echo(f"Provider: {row['provider_id']}")
    typer.echo(f"Version: {row['provider_version']}")
    typer.echo(f"Title: {row['title']}")
    typer.echo(f"Languages: {', '.join(row['supported_languages'])}")
    typer.echo(f"Frameworks: {', '.join(row['supported_frameworks']) or '(none)'}")
    typer.echo("Capabilities:")
    for item in row["capabilities_supported"]:
        typer.echo(f"  - {item['capability_id']} ({item['maturity']})")
    if row["capabilities_unsupported"]:
        typer.echo("Unsupported:")
        for item in row["capabilities_unsupported"]:
            typer.echo(f"  - {item}")


@providers_app.command("explain")
def explain_provider(
    provider_id: Annotated[str, typer.Argument(help="Provider ID.")],
    repository: Annotated[
        Path,
        typer.Option("--repository", help="Repository root to evaluate applicability."),
    ] = Path("."),
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to codestrata.toml."),
    ] = Path("codestrata.toml"),
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
) -> None:
    """Explain provider applicability for a repository path listing."""

    settings = _load_optional_settings(config)
    service = create_language_evidence_service(settings)
    paths = _list_source_paths(repository)
    try:
        payload = service.explain_provider(provider_id, relative_paths=paths, file_texts={})
    except Exception as error:  # noqa: BLE001
        typer.echo(redact_secrets(str(error)), err=True)
        raise typer.Exit(code=1) from error
    # Without texts, explain still reports language presence via paths in evaluate —
    # re-run with empty texts may yield insufficient_input; that is intentional.
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    typer.echo(f"{payload['provider_id']}: {payload['status']}")
    if payload.get("message"):
        typer.echo(payload["message"])


@evidence_app.command("capabilities")
def list_capabilities(
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
) -> None:
    """List known language evidence capability identifiers."""

    caps = [
        CAP_SOURCE_FILES,
        CAP_DEPENDENCIES_IMPORTS,
        CAP_DEPENDENCIES_TYPE_ONLY,
        CAP_ARCHITECTURE_UNITS,
        CAP_ARCHITECTURE_LAYERS,
        CAP_FRAMEWORK_USAGE,
    ]
    if json_output:
        typer.echo(json.dumps({"capabilities": caps}, indent=2))
        return
    for item in caps:
        typer.echo(item)


@evidence_app.command("plan")
def plan_providers(
    repository: Annotated[
        Path,
        typer.Option("--repository", help="Repository root."),
    ] = Path("."),
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to codestrata.toml."),
    ] = Path("codestrata.toml"),
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
) -> None:
    """Plan which language evidence providers would run."""

    settings = _load_optional_settings(config)
    service = create_language_evidence_service(settings)
    paths = _list_source_paths(repository)
    # Provide empty texts so planners can still detect languages from paths;
    # providers requiring text become insufficient_input — reported in skipped.
    plan = service.plan(
        repository_id=repository.name or "repository",
        relative_paths=paths,
        file_texts={},
    )
    payload = plan.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    typer.echo(f"Detected languages: {', '.join(plan.detected_languages) or '(none)'}")
    typer.echo(f"Applicable: {', '.join(plan.applicable_provider_ids) or '(none)'}")
    for skipped in plan.skipped:
        typer.echo(f"Skipped {skipped.provider_id}: {skipped.status} ({skipped.reason})")


def _load_optional_settings(config: Path) -> CodestrataSettings | None:
    if config.exists():
        return load_settings(config)
    return None


def _list_source_paths(repository: Path) -> list[str]:
    root = repository.expanduser().resolve()
    if not root.is_dir():
        return []
    suffixes = {".py", ".java", ".js", ".jsx", ".ts", ".tsx", ".php"}
    paths: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in suffixes:
            continue
        relative = path.relative_to(root).as_posix()
        lower = f"/{relative.lower()}"
        if any(
            marker in lower
            for marker in ("/node_modules/", "/.git/", "/target/", "/dist/", "/build/")
        ):
            continue
        paths.append(relative)
        if len(paths) >= 5000:
            break
    return paths


@evidence_app.command("init")
def init_evidence_plan(
    repository: Annotated[
        Path,
        typer.Option("--repo", "--repository", help="Repository to observe."),
    ] = Path("."),
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Evidence-plan YAML path."),
    ] = Path("evidence-plan.yaml"),
    goal: Annotated[
        str,
        typer.Option("--goal", help="Decision or question this evidence should support."),
    ] = "Understand the repository evidence available for an engineering decision",
    force: Annotated[
        bool,
        typer.Option("--force", help="Replace an existing plan file."),
    ] = False,
) -> None:
    """Create a versioned, editable evidence plan from safe local defaults."""

    if output.exists() and not force:
        typer.echo(f"Plan already exists: {output}. Use --force to replace it.", err=True)
        raise typer.Exit(code=1)
    service = EvidenceFrameworkService()
    plan = service.create_default_plan(repository, goal=goal)
    destination = service.save_plan(plan, output)
    typer.echo(f"Evidence plan written: {destination.resolve()}")


@evidence_app.command("preview")
def preview_evidence_plan(
    plan_path: Annotated[
        Path,
        typer.Option("--plan", "-p", help="Evidence-plan YAML path."),
    ] = Path("evidence-plan.yaml"),
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
) -> None:
    """Explain reads, execution, network behavior, applicability, and blind spots."""

    service = EvidenceFrameworkService()
    try:
        plan = service.load_plan(plan_path)
        preview = service.preview(plan)
    except Exception as error:  # noqa: BLE001 - CLI boundary
        typer.echo(redact_secrets(str(error)), err=True)
        raise typer.Exit(code=2) from error
    if json_output:
        typer.echo(preview.model_dump_json(indent=2))
        return
    typer.echo(f"Plan: {preview.plan_id}")
    typer.echo("Reads:")
    for read_description in preview.reads:
        typer.echo(f"  - {read_description}")
    typer.echo("Executes:")
    for execution_description in preview.executes or ("Nothing",):
        typer.echo(f"  - {execution_description}")
    typer.echo("Leaves this machine:")
    for network_description in preview.leaves_machine:
        typer.echo(f"  - {network_description}")
    typer.echo("Activities:")
    for collector_preview in preview.collectors:
        typer.echo(
            f"  - {collector_preview.activity_id}: {collector_preview.status} — "
            f"{collector_preview.reason}"
        )


@evidence_app.command("run")
def run_evidence_plan(
    plan_path: Annotated[
        Path,
        typer.Option("--plan", "-p", help="Evidence-plan YAML path."),
    ] = Path("evidence-plan.yaml"),
    output_root: Annotated[
        Path,
        typer.Option("--output", "-o", help="Portable artifact store root."),
    ] = Path(".codestrata-artifacts"),
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON summary.")] = False,
) -> None:
    """Collect, normalize, assess, and report a reviewed evidence plan."""

    service = EvidenceFrameworkService()
    try:
        plan = service.load_plan(plan_path)
        result = service.run(plan, output_root=output_root)
    except Exception as error:  # noqa: BLE001 - CLI boundary
        typer.echo(redact_secrets(str(error)), err=True)
        raise typer.Exit(code=1) from error
    if json_output:
        typer.echo(
            json.dumps(
                {
                    "run": result.run.model_dump(mode="json"),
                    "evidence_count": len(result.evidence),
                    "finding_count": len(result.assessment.findings),
                    "action_count": len(result.assessment.actions),
                    "output_directory": str(result.output_directory),
                    "report": str(result.output_directory / "report.html"),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return
    typer.echo(f"Run {result.run.status.value}: {result.run.run_id}")
    typer.echo(f"Evidence: {len(result.evidence)} normalized record(s)")
    typer.echo(
        f"Assessment: {len(result.assessment.findings)} finding(s), "
        f"{len(result.assessment.actions)} action(s)"
    )
    typer.echo(f"Report: {(result.output_directory / 'report.html').resolve()}")


@evidence_app.command("studio")
def evidence_studio(
    repository: Annotated[
        Path,
        typer.Option("--repo", "--repository", help="Repository to observe."),
    ] = Path("."),
    port: Annotated[
        int,
        typer.Option("--port", min=0, max=65535, help="Loopback port; 0 chooses one."),
    ] = 8765,
    open_browser: Annotated[
        bool,
        typer.Option("--open/--no-open", help="Open the local studio in a browser."),
    ] = True,
) -> None:
    """Open the goal-first local Evidence Studio; no account or cloud required."""

    server = EvidenceStudioServer(repository=repository, port=port)
    try:
        server.start()
    except OSError as error:
        typer.echo(f"Could not start Evidence Studio: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Evidence Studio: {server.url}")
    typer.echo(
        "Collected evidence stays local. GitHub acquisition and reviewed external "
        "activities are the only network paths."
    )
    typer.echo("Press Ctrl+C to stop.")
    if open_browser:
        webbrowser.open(server.url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        typer.echo("\nEvidence Studio stopped.")
    finally:
        server.shutdown()
