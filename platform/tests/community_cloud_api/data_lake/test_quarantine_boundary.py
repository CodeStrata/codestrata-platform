"""Architecture / import boundary for quarantine (Slice 8.9)."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
PLATFORM_SRC = REPO_ROOT / "platform" / "src" / "codestrata_platform"
COMMUNITY_CLOUD_API_PKG = PLATFORM_SRC / "community_cloud_api"
DATA_LAKE_PKG = COMMUNITY_CLOUD_API_PKG / "data_lake"
DEPLOYMENT_WIRING = COMMUNITY_CLOUD_API_PKG / "deployment" / "wiring.py"
APP_PY = COMMUNITY_CLOUD_API_PKG / "app.py"


def test_quarantine_modules_exist() -> None:
    for name in (
        "quarantine_policy.py",
        "quarantine_models.py",
        "quarantine_identity.py",
        "quarantine_validation.py",
        "quarantine_serialization.py",
        "quarantine_diagnostics.py",
        "quarantine_receipts.py",
        "quarantine_projection.py",
        "quarantine_error_mapping.py",
    ):
        assert (DATA_LAKE_PKG / name).is_file()


def test_app_and_wiring_do_not_import_quarantine() -> None:
    for path in (APP_PY, DEPLOYMENT_WIRING):
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "quarantine" not in node.module
                assert "data_lake" not in node.module or "infrastructure" not in (
                    node.module or ""
                )


def test_quarantine_domain_modules_do_not_import_boto3() -> None:
    for path in DATA_LAKE_PKG.glob("quarantine_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "boto3"
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("boto3")


def test_s3_store_no_longer_exports_quarantine_not_implemented_stub() -> None:
    from codestrata_platform.community_cloud_api.data_lake.infrastructure import s3_store

    assert not hasattr(s3_store, "QUARANTINE_NOT_IMPLEMENTED_DETAIL")
