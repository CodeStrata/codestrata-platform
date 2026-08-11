"""Ownership boundary checks for Community Data Lake completion (Slice 8.15)."""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

from verification.community_data_lake_completion.models import CheckResult

REPO = Path(__file__).resolve().parents[3]
ENGINE_SRC = REPO / "engine" / "src" / "codestrata"
VSCODE_SRC = REPO / "vscode-plugin" / "src"
CURSOR_SRC = REPO / "cursor-plugin" / "src"
MANIFEST = REPO / "public-export-manifest.yaml"

_FORBIDDEN_CLI_COMMANDS = frozenset(
    {
        "data-lake",
        "upload-events",
        "flush-events",
        "cloud-sync",
        "lake-status",
        "quarantine",
    }
)

_PLUGIN_FORBIDDEN_TOKENS = (
    "community-data-lake",
    "community_cloud_api.data_lake",
    "import boto3",
)


def _collect_typer_command_names(app: object) -> set[str]:
    names: set[str] = set()
    registered = getattr(app, "registered_commands", None)
    if registered:
        for cmd in registered:
            name = getattr(cmd, "name", None)
            if name:
                names.add(name)
    registered_groups = getattr(app, "registered_groups", None)
    if registered_groups:
        for group in registered_groups:
            typer_instance = getattr(group, "typer_instance", None)
            if typer_instance is not None:
                names.update(_collect_typer_command_names(typer_instance))
    return names


def check_boundaries() -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.extend(_check_engine_ast())
    checks.extend(_check_cli_commands())
    checks.extend(_check_plugin_sources(VSCODE_SRC, label="vscode"))
    checks.extend(_check_plugin_sources(CURSOR_SRC, label="cursor"))
    checks.extend(_check_public_export_manifest())
    checks.extend(_check_production_route_count())
    return checks


def _check_engine_ast() -> list[CheckResult]:
    import_offenders: list[str] = []
    token_offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "community_cloud_api.data_lake" in text:
            token_offenders.append(str(path.relative_to(REPO)))
        if "infrastructure.modules.community-data-lake" in text:
            token_offenders.append(str(path.relative_to(REPO)))
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "community_cloud_api.data_lake" in node.module:
                    import_offenders.append(str(path.relative_to(REPO)))
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "community_cloud_api.data_lake" in alias.name:
                        import_offenders.append(str(path.relative_to(REPO)))
    return [
        CheckResult(
            name="boundary:engine_no_data_lake_import",
            ok=not import_offenders,
            detail=",".join(sorted(set(import_offenders))) or "clean",
            category="boundary",
        ),
        CheckResult(
            name="boundary:engine_no_data_lake_tokens",
            ok=not token_offenders,
            detail=",".join(sorted(set(token_offenders))) or "clean",
            category="boundary",
        ),
    ]


def _check_cli_commands() -> list[CheckResult]:
    from codestrata.cli import app

    command_names = _collect_typer_command_names(app)
    forbidden_hits = sorted(command_names & _FORBIDDEN_CLI_COMMANDS)
    return [
        CheckResult(
            name="boundary:cli_no_data_lake_commands",
            ok=not forbidden_hits,
            detail=",".join(forbidden_hits) or "clean",
            category="boundary",
        )
    ]


def _check_plugin_sources(root: Path, *, label: str) -> list[CheckResult]:
    if not root.is_dir():
        if label == "cursor":
            return [
                CheckResult(
                    name=f"boundary:{label}:plugin_src_present",
                    ok=True,
                    detail="retired",
                    category="boundary",
                )
            ]
        return [
            CheckResult(
                name=f"boundary:{label}:plugin_src_present",
                ok=False,
                detail="missing",
                category="boundary",
            )
        ]
    offenders: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        text = path.read_text(encoding="utf-8")
        for token in _PLUGIN_FORBIDDEN_TOKENS:
            if token in text:
                offenders.append(f"{path.relative_to(REPO)}:{token}")
    return [
        CheckResult(
            name=f"boundary:{label}:no_data_lake_tokens",
            ok=not offenders,
            detail=",".join(offenders[:6]) or "clean",
            category="boundary",
        )
    ]


def _check_public_export_manifest() -> list[CheckResult]:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    return [
        CheckResult(
            name="boundary:public_export_excludes_platform",
            ok="platform/" in forbidden,
            detail="platform/",
            category="boundary",
        ),
        CheckResult(
            name="boundary:public_export_excludes_infrastructure",
            ok="infrastructure/" in forbidden,
            detail="infrastructure/",
            category="boundary",
        ),
    ]


def _check_production_route_count() -> list[CheckResult]:
    from codestrata_platform.community_cloud_api.deployment import (
        create_production_foundation_app,
        load_deployment_settings,
    )

    app = create_production_foundation_app(settings=load_deployment_settings({}))
    count = app.state.community_cloud_route_registry.diagnostics().registered_route_count
    return [
        CheckResult(
            name="boundary:production_ingestion_and_insights_routes",
            ok=count == 19,
            detail=f"count={count}",
            category="boundary",
        )
    ]


__all__ = ["check_boundaries"]
