"""Architecture / import boundary for retention policy (Slice 8.10)."""

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

_RETENTION_MODULES = (
    "retention_policy.py",
    "retention_validation.py",
    "retention_diagnostics.py",
)


def test_retention_modules_exist() -> None:
    for name in _RETENTION_MODULES:
        assert (DATA_LAKE_PKG / name).is_file()


def test_app_and_wiring_have_no_retention_or_data_lake() -> None:
    for path in (APP_PY, DEPLOYMENT_WIRING):
        text = path.read_text(encoding="utf-8")
        assert "retention_policy" not in text
        assert "data_lake" not in text
        assert "CommunityDataLakeRetentionPolicy" not in text


def test_engine_unchanged_by_retention() -> None:
    forbidden = (
        "CommunityDataLakeRetentionPolicy",
        "community-data-lake-retention-policy",
        "retention_policy",
        "community_cloud_api.data_lake",
    )
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_retention_policy_does_not_import_infrastructure() -> None:
    for name in _RETENTION_MODULES:
        path = DATA_LAKE_PKG / name
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "infrastructure" not in node.module, f"{path}: {node.module}"
                assert "boto3" not in node.module, f"{path}: {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "boto3"
                    assert "infrastructure" not in alias.name


def test_production_fail_closed_symbols_unchanged() -> None:
    from codestrata_platform.community_cloud_api.deployment.settings import (
        load_deployment_settings,
    )
    from codestrata_platform.community_cloud_api.deployment.wiring import (
        create_production_foundation_app,
    )

    settings = load_deployment_settings({})
    app = create_production_foundation_app(settings=settings)
    registry = app.state.community_cloud_route_registry
    assert {(r.method, r.path) for r in registry.list_routes()} == {
        ("GET", "/health"),
        ("POST", "/ai-usage"),
        ("POST", "/assessment-metadata"),
        ("POST", "/cli-events"),
        ("POST", "/extension-events"),
        ("POST", "/telemetry"),
    }
    # Retention is not part of production foundation wiring.
    wiring_text = DEPLOYMENT_WIRING.read_text(encoding="utf-8")
    assert "retention" not in wiring_text.lower()
    assert "data_lake" not in wiring_text
