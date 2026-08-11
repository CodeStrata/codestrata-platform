"""Architecture / import boundary for access policy (Slice 8.12)."""

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

_ACCESS_MODULES = (
    "access_policy.py",
    "access_validation.py",
    "access_diagnostics.py",
)


def test_access_modules_exist() -> None:
    for name in _ACCESS_MODULES:
        assert (DATA_LAKE_PKG / name).is_file()


def test_app_has_no_access_policy_and_wiring_is_gated() -> None:
    app_text = APP_PY.read_text(encoding="utf-8")
    assert "access_policy" not in app_text
    assert "data_lake" not in app_text
    assert "CommunityDataLakeAccessPolicy" not in app_text
    assert "writer_policy_attached" not in app_text
    assert "ListBucket" not in app_text
    wiring_text = DEPLOYMENT_WIRING.read_text(encoding="utf-8")
    assert "access_policy" not in wiring_text
    assert "ingestion_enabled" in wiring_text
    assert "CommunityDataLakeAccessPolicy" not in wiring_text
    assert "writer_policy_attached" not in wiring_text
    assert "ListBucket" not in wiring_text


def test_engine_unchanged_by_access() -> None:
    forbidden = (
        "CommunityDataLakeAccessPolicy",
        "community-data-lake-access-policy",
        "access_policy",
        "community_cloud_api.data_lake",
    )
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_access_policy_does_not_import_infrastructure() -> None:
    for name in _ACCESS_MODULES:
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
    assert {(r.method, r.path) for r in registry.list_routes()} >= {
        ("GET", "/health"),
        ("POST", "/ai-usage"),
        ("POST", "/assessment-metadata"),
        ("POST", "/cli-events"),
        ("POST", "/extension-events"),
        ("POST", "/telemetry"),
    }
    wiring_text = DEPLOYMENT_WIRING.read_text(encoding="utf-8")
    assert "access_policy" not in wiring_text
    assert "ingestion_enabled" in wiring_text
    assert "ListBucket" not in wiring_text


def test_package_exports_access_symbols() -> None:
    import codestrata_platform.community_cloud_api.data_lake as data_lake

    assert data_lake.COMMUNITY_DATA_LAKE_ACCESS_POLICY_URN == (
        "community-data-lake-access-policy:1.0"
    )
    assert data_lake.default_access_policy().writer_policy_attached is False
    assert "CommunityDataLakeAccessPolicy" in data_lake.__all__
    assert "validate_access_action_sets" in data_lake.__all__
    assert "AccessPolicyDiagnostics" in data_lake.__all__


def test_access_diagnostics_contract_has_no_iam_identifiers() -> None:
    from codestrata_platform.community_cloud_api.data_lake.access_diagnostics import (
        diagnostics_from_access_policy,
    )
    from codestrata_platform.community_cloud_api.data_lake.access_policy import (
        default_access_policy,
    )

    diag = diagnostics_from_access_policy(default_access_policy()).to_stable_dict()
    assert diag["writer_attached"] is False
    assert "writer_policy_arn" not in diag
    assert "bucket_arn" not in diag
