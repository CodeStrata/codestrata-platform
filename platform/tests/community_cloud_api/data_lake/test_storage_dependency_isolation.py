"""Storage abstraction dependency isolation tests (Slice 8.13)."""

from __future__ import annotations

import ast
from pathlib import Path

import codestrata_platform.community_cloud_api.data_lake as data_lake_pkg

REPO_ROOT = Path(__file__).resolve().parents[4]
ENGINE_SRC = REPO_ROOT / "engine" / "src" / "codestrata"
PLATFORM_SRC = REPO_ROOT / "platform" / "src" / "codestrata_platform"
COMMUNITY_CLOUD_API_PKG = PLATFORM_SRC / "community_cloud_api"
DATA_LAKE_PKG = COMMUNITY_CLOUD_API_PKG / "data_lake"
DEPLOYMENT_WIRING = COMMUNITY_CLOUD_API_PKG / "deployment" / "wiring.py"
APP_PY = COMMUNITY_CLOUD_API_PKG / "app.py"

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

_FORBIDDEN_IMPORTS = ("boto3", "botocore")


def test_storage_domain_modules_have_no_boto3_or_botocore_imports() -> None:
    offenders: list[str] = []
    for path in DATA_LAKE_PKG.glob("*.py"):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for token in _FORBIDDEN_IMPORTS:
                    if token in node.module:
                        offenders.append(f"{path.name}:from {node.module}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for token in _FORBIDDEN_IMPORTS:
                        if alias.name == token or alias.name.startswith(f"{token}."):
                            offenders.append(f"{path.name}:import {alias.name}")
    assert offenders == []


def test_storage_modules_exist() -> None:
    for name in _STORAGE_MODULES:
        assert (DATA_LAKE_PKG / name).is_file()


def test_platform_import_succeeds() -> None:
    assert data_lake_pkg.COMMUNITY_DATA_LAKE_STORAGE_POLICY_URN == (
        "community-data-lake-storage-policy:1.0"
    )
    assert callable(data_lake_pkg.create_community_data_lake_store)


def test_engine_has_no_data_lake() -> None:
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


def test_app_and_wiring_have_no_storage_factory() -> None:
    for path in (APP_PY, DEPLOYMENT_WIRING):
        text = path.read_text(encoding="utf-8")
        assert "storage_factory" not in text
        assert "create_community_data_lake_store" not in text
        assert "CommunityDataLakeStoragePolicy" not in text
        assert "data_lake" not in text
