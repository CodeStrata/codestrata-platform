"""Architecture / import boundary for storage abstraction (Slice 8.13)."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
ENGINE_SRC = REPO_ROOT / "engine" / "src" / "codestrata"
PLATFORM_SRC = REPO_ROOT / "platform" / "src" / "codestrata_platform"
COMMUNITY_CLOUD_API_PKG = PLATFORM_SRC / "community_cloud_api"
DATA_LAKE_PKG = COMMUNITY_CLOUD_API_PKG / "data_lake"
DEPLOYMENT_WIRING = COMMUNITY_CLOUD_API_PKG / "deployment" / "wiring.py"
APP_PY = COMMUNITY_CLOUD_API_PKG / "app.py"
MODULE = REPO_ROOT / "infrastructure" / "modules" / "community-data-lake"
PORTS_PY = DATA_LAKE_PKG / "ports.py"

_STORAGE_MODULES = (
    "storage.py",
    "storage_capabilities.py",
    "storage_configuration.py",
    "storage_factory.py",
    "storage_results.py",
    "storage_errors.py",
    "storage_diagnostics.py",
    "storage_validation.py",
)

_FORBIDDEN_PORT_METHODS = (
    "list_objects",
    "delete_object",
    "delete",
    "update_object",
    "copy_object",
)


def test_storage_modules_exist() -> None:
    for name in _STORAGE_MODULES:
        assert (DATA_LAKE_PKG / name).is_file()


def test_app_has_no_storage_factory_and_wiring_is_gated() -> None:
    app_text = APP_PY.read_text(encoding="utf-8")
    assert "storage_factory" not in app_text
    assert "create_community_data_lake_store" not in app_text

    wiring_text = DEPLOYMENT_WIRING.read_text(encoding="utf-8")
    # Slice 17.7: wiring may import data_lake only on the gated ingestion path.
    assert "ingestion_enabled" in wiring_text
    assert "UnavailableCommunityCredentialVerifier" in wiring_text
    assert "InMemoryTelemetryEventSink" not in wiring_text
    assert "CommunityDataLakeStoragePolicy" not in wiring_text


def test_engine_unchanged_by_storage_abstraction() -> None:
    forbidden = (
        "CommunityDataLakeStoragePolicy",
        "community-data-lake-storage-policy",
        "storage_factory",
        "create_community_data_lake_store",
        "community_cloud_api.data_lake",
    )
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_storage_policy_modules_do_not_import_infrastructure() -> None:
    for name in _STORAGE_MODULES:
        if name == "storage_factory.py":
            continue
        path = DATA_LAKE_PKG / name
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "infrastructure" not in node.module, f"{path}: {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "infrastructure" not in alias.name


def test_production_fail_closed_symbols_unchanged() -> None:
    from codestrata_platform.community_cloud_api.deployment.settings import (
        load_deployment_settings,
    )
    from codestrata_platform.community_cloud_api.deployment.wiring import (
        create_production_foundation_app,
    )

    settings = load_deployment_settings({})
    assert settings.ingestion_enabled is False
    app = create_production_foundation_app(settings=settings)
    registry = app.state.community_cloud_route_registry
    routes = {(r.method, r.path) for r in registry.list_routes()}
    assert ("GET", "/health") in routes
    assert ("POST", "/telemetry") in routes
    assert ("POST", "/ai-usage") in routes
    wiring_text = DEPLOYMENT_WIRING.read_text(encoding="utf-8")
    assert "ingestion_enabled" in wiring_text
    assert "UnavailableCommunityCredentialVerifier" in wiring_text
    assert "InMemoryTelemetryEventSink" not in wiring_text


def test_package_exports_storage_symbols() -> None:
    import codestrata_platform.community_cloud_api.data_lake as data_lake

    assert data_lake.COMMUNITY_DATA_LAKE_STORAGE_POLICY_URN == (
        "community-data-lake-storage-policy:1.0"
    )
    assert data_lake.default_storage_policy().production_default_unavailable is True
    assert "CommunityDataLakeStoragePolicy" in data_lake.__all__
    assert "create_community_data_lake_store" in data_lake.__all__
    assert "StorageAbstractionDiagnostics" in data_lake.__all__
    assert "validate_storage_policy_invariants" in data_lake.__all__


def test_protocol_source_has_no_list_or_delete_methods() -> None:
    source = PORTS_PY.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(PORTS_PY))
    protocol_methods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "CommunityDataLakeStore":
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    protocol_methods.append(item.name)
    for forbidden in _FORBIDDEN_PORT_METHODS:
        assert forbidden not in protocol_methods
    assert "put_immutable_storage_object" in protocol_methods
    assert "put_immutable_quarantine_object" in protocol_methods


def test_iam_still_put_and_get_only_no_list_bucket() -> None:
    from codestrata_platform.community_cloud_api.data_lake.access_policy import (
        default_access_policy,
    )

    policy = default_access_policy()
    assert policy.writer_allowed_actions == frozenset({"s3:PutObject", "s3:GetObject"})
    iam = (MODULE / "iam.tf").read_text(encoding="utf-8")
    assert "s3:PutObject" in iam
    assert "s3:GetObject" in iam
    assert "s3:ListBucket" in iam
    assert "ListApprovedWriterPrefixes" in iam
    assert "s3:prefix" in iam
    assert "s3:listallmybuckets" not in iam.lower()


def test_storage_diagnostics_contract_has_no_bucket_or_key() -> None:
    from codestrata_platform.community_cloud_api.data_lake.storage_capabilities import (
        StorageCapabilities,
    )
    from codestrata_platform.community_cloud_api.data_lake.storage_configuration import (
        StorageAdapterType,
    )
    from codestrata_platform.community_cloud_api.data_lake.storage_diagnostics import (
        diagnostics_from_storage,
    )
    from codestrata_platform.community_cloud_api.data_lake.storage import (
        default_storage_policy,
    )

    diag = diagnostics_from_storage(
        policy=default_storage_policy(),
        adapter_type=StorageAdapterType.UNAVAILABLE,
        capabilities=StorageCapabilities.for_unavailable(),
    ).to_stable_dict()
    assert "bucket" not in diag
    assert "object_key" not in diag
    assert "arn" not in diag
