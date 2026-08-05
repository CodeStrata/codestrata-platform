"""Architecture / import boundary for encryption policy (Slice 8.11)."""

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

_ENCRYPTION_MODULES = (
    "encryption_policy.py",
    "encryption_validation.py",
    "encryption_diagnostics.py",
)


def test_encryption_modules_exist() -> None:
    for name in _ENCRYPTION_MODULES:
        assert (DATA_LAKE_PKG / name).is_file()


def test_app_and_wiring_have_no_encryption_or_data_lake() -> None:
    for path in (APP_PY, DEPLOYMENT_WIRING):
        text = path.read_text(encoding="utf-8")
        assert "encryption_policy" not in text
        assert "data_lake" not in text
        assert "CommunityDataLakeEncryptionPolicy" not in text
        assert "SSEKMSKeyId" not in text
        assert "kms_key_id" not in text


def test_engine_unchanged_by_encryption() -> None:
    forbidden = (
        "CommunityDataLakeEncryptionPolicy",
        "community-data-lake-encryption-policy",
        "encryption_policy",
        "community_cloud_api.data_lake",
    )
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_encryption_policy_does_not_import_infrastructure() -> None:
    for name in _ENCRYPTION_MODULES:
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
    wiring_text = DEPLOYMENT_WIRING.read_text(encoding="utf-8")
    assert "encryption" not in wiring_text.lower()
    assert "data_lake" not in wiring_text
    assert "kms" not in wiring_text.lower()


def test_package_exports_encryption_symbols() -> None:
    import codestrata_platform.community_cloud_api.data_lake as data_lake

    assert data_lake.COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_URN == (
        "community-data-lake-encryption-policy:1.0"
    )
    assert data_lake.default_encryption_policy().encryption_mode == "sse_s3"
    assert "CommunityDataLakeEncryptionPolicy" in data_lake.__all__
    assert "validate_encryption_mode" in data_lake.__all__
    assert "EncryptionPolicyDiagnostics" in data_lake.__all__


def test_no_kms_in_product_receipt_or_diagnostics_contracts() -> None:
    from codestrata_platform.community_cloud_api.data_lake.encryption_diagnostics import (
        diagnostics_from_encryption_policy,
    )
    from codestrata_platform.community_cloud_api.data_lake.encryption_policy import (
        default_encryption_policy,
    )

    diag = diagnostics_from_encryption_policy(default_encryption_policy()).to_stable_dict()
    assert diag["kms_enabled"] is False
    assert "kms_key_id" not in diag
    assert "key_arn" not in diag
