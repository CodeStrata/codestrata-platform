"""Architecture boundary: Community Data Lake is Platform-only, unwired (Slice 8.1 / 8.2)."""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
ENGINE_SRC = REPO_ROOT / "engine" / "src" / "codestrata"
PLATFORM_SRC = REPO_ROOT / "platform" / "src" / "codestrata_platform"
COMMUNITY_CLOUD_API_PKG = PLATFORM_SRC / "community_cloud_api"
DATA_LAKE_PKG = COMMUNITY_CLOUD_API_PKG / "data_lake"
DATA_LAKE_INFRASTRUCTURE_PKG = DATA_LAKE_PKG / "infrastructure"


def _is_under_infrastructure(path: Path) -> bool:
    return DATA_LAKE_INFRASTRUCTURE_PKG in path.parents


def _domain_modules() -> list[Path]:
    """``data_lake/*.py`` files only — excludes the ``infrastructure/`` subpackage."""

    return [path for path in DATA_LAKE_PKG.rglob("*.py") if not _is_under_infrastructure(path)]


def test_data_lake_package_exists_under_platform_only() -> None:
    assert DATA_LAKE_PKG.is_dir()
    assert (DATA_LAKE_PKG / "__init__.py").is_file()
    assert (DATA_LAKE_PKG / "enums.py").is_file()
    assert (DATA_LAKE_PKG / "policy.py").is_file()
    assert (DATA_LAKE_PKG / "identifiers.py").is_file()
    assert (DATA_LAKE_PKG / "envelopes.py").is_file()
    assert (DATA_LAKE_PKG / "partitions.py").is_file()
    assert (DATA_LAKE_PKG / "ports.py").is_file()
    assert (DATA_LAKE_PKG / "validation.py").is_file()
    assert (DATA_LAKE_PKG / "diagnostics.py").is_file()
    assert (DATA_LAKE_PKG / "models.py").is_file()
    assert (DATA_LAKE_PKG / "canonical_json.py").is_file()
    assert (DATA_LAKE_PKG / "objects.py").is_file()
    assert (DATA_LAKE_PKG / "receipts.py").is_file()
    assert (DATA_LAKE_PKG / "decisions.py").is_file()
    assert (DATA_LAKE_PKG / "immutable_write.py").is_file()
    assert (DATA_LAKE_PKG / "errors.py").is_file()
    assert (DATA_LAKE_PKG / "quarantine_policy.py").is_file()
    assert (DATA_LAKE_PKG / "quarantine_models.py").is_file()
    assert (DATA_LAKE_PKG / "quarantine_projection.py").is_file()
    assert not list(ENGINE_SRC.rglob("*data_lake*"))


def test_data_lake_infrastructure_subpackage_exists() -> None:
    assert DATA_LAKE_INFRASTRUCTURE_PKG.is_dir()
    assert (DATA_LAKE_INFRASTRUCTURE_PKG / "__init__.py").is_file()
    assert (DATA_LAKE_INFRASTRUCTURE_PKG / "s3_store.py").is_file()
    assert (DATA_LAKE_INFRASTRUCTURE_PKG / "client.py").is_file()
    assert (DATA_LAKE_INFRASTRUCTURE_PKG / "configuration.py").is_file()
    assert (DATA_LAKE_INFRASTRUCTURE_PKG / "error_mapping.py").is_file()
    assert (DATA_LAKE_INFRASTRUCTURE_PKG / "diagnostics.py").is_file()


def test_engine_ast_does_not_import_data_lake() -> None:
    for path in ENGINE_SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "data_lake" not in node.module, f"{path}: {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "data_lake" not in alias.name, f"{path}: {alias.name}"


def test_engine_has_no_community_data_lake_tokens() -> None:
    forbidden = (
        "community-data-lake-policy",
        "CommunityDataLakePolicy",
        "community_cloud_api.data_lake",
        "InMemoryCommunityDataLakeStore",
        "lake-object:",
    )
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_data_lake_domain_modules_have_no_boto3_import() -> None:
    """``boto3`` is banned in every ``data_lake/*.py`` domain module.

    The ONLY exception is the ``infrastructure/`` subpackage (Slice 8.2),
    checked separately below.
    """

    for path in _domain_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "boto3" not in node.module, f"{path}: {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "boto3" not in alias.name, f"{path}: {alias.name}"


def test_data_lake_domain_modules_have_no_boto3_import_statement_text() -> None:
    # Docstrings may reference "boto3" by name to document the boundary;
    # only an actual import statement is disallowed.
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in _domain_modules()
        if "import boto3" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_boto3_import_confined_to_infrastructure_subpackage() -> None:
    """Any ``import boto3`` text anywhere under ``data_lake/`` must live under ``infrastructure/``."""

    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in DATA_LAKE_PKG.rglob("*.py")
        if _is_under_infrastructure(path) is False and "import boto3" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_data_lake_infrastructure_client_imports_boto3_lazily() -> None:
    """``client.py`` is allowed (and expected) to import boto3 — but only inside a function body."""

    client_path = DATA_LAKE_INFRASTRUCTURE_PKG / "client.py"
    text = client_path.read_text(encoding="utf-8")
    assert "import boto3" in text
    tree = ast.parse(text, filename=str(client_path))
    module_level_boto3_imports = [
        node
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.Import) and any(alias.name == "boto3" for alias in node.names)
    ]
    assert module_level_boto3_imports == [], "boto3 must be imported lazily inside a function, not at module level"


def test_data_lake_not_referenced_by_app_or_registry() -> None:
    targets = (
        COMMUNITY_CLOUD_API_PKG / "app.py",
        COMMUNITY_CLOUD_API_PKG / "registry.py",
    )
    offenders: list[str] = []
    for target in targets:
        text = target.read_text(encoding="utf-8")
        if "data_lake" in text:
            offenders.append(str(target.relative_to(REPO_ROOT)))
    wiring = COMMUNITY_CLOUD_API_PKG / "deployment" / "wiring.py"
    assert "ingestion_enabled" in wiring.read_text(encoding="utf-8")
    assert offenders == []


def test_data_lake_package_has_no_routes_module() -> None:
    assert not (DATA_LAKE_PKG / "routes.py").exists()
    assert not (DATA_LAKE_PKG / "service.py").exists()


def test_production_routes_unaffected_by_data_lake_package() -> None:
    from codestrata_platform.community_cloud_api.deployment.settings import (
        load_deployment_settings,
    )
    from codestrata_platform.community_cloud_api.deployment.wiring import (
        create_production_foundation_app,
    )

    app = create_production_foundation_app(settings=load_deployment_settings({}))
    registry = app.state.community_cloud_route_registry
    assert {(r.method, r.path) for r in registry.list_routes()} >= {
        ("GET", "/health"),
        ("POST", "/ai-usage"),
        ("POST", "/assessment-metadata"),
        ("POST", "/cli-events"),
        ("POST", "/extension-events"),
        ("POST", "/telemetry"),
    }


def test_public_export_excludes_platform_package() -> None:
    blob = (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    manifest = yaml.safe_load(blob)
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    assert "platform/" in forbidden


def test_data_lake_constants_present_and_versioned() -> None:
    from codestrata_platform.community_cloud_api.constants import (
        COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION,
        COMMUNITY_DATA_LAKE_POLICY_VERSION,
    )

    assert COMMUNITY_DATA_LAKE_POLICY_VERSION == "1.0"
    assert COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION == "1.0"


def test_data_lake_package_not_exported_from_top_level_init() -> None:
    # Slice 8.1 intentionally does not wire the data lake domain into the
    # top-level Community Cloud API package surface (no app/endpoint wiring).
    top_level_init = (COMMUNITY_CLOUD_API_PKG / "__init__.py").read_text(encoding="utf-8")
    assert "data_lake" not in top_level_init
