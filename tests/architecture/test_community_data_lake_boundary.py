"""Architecture boundary: Community Data Lake is Platform-only (Slice 8.15)."""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_SRC = REPO_ROOT / "engine" / "src" / "codestrata"
PLATFORM_SRC = REPO_ROOT / "platform" / "src" / "codestrata_platform"
DATA_LAKE_PKG = PLATFORM_SRC / "community_cloud_api" / "data_lake"


def test_engine_has_no_data_lake_package() -> None:
    assert not list(ENGINE_SRC.rglob("*data_lake*"))


def test_engine_ast_does_not_import_data_lake() -> None:
    for path in ENGINE_SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "data_lake" not in node.module, f"{path}: {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "data_lake" not in alias.name, f"{path}: {alias.name}"


def test_public_export_excludes_platform_and_infrastructure() -> None:
    manifest = yaml.safe_load(
        (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    assert "platform/" in forbidden
    assert "infrastructure/" in forbidden


def test_no_duplicate_data_lake_outside_platform_src() -> None:
    allowed = DATA_LAKE_PKG
    offenders: list[str] = []
    for path in REPO_ROOT.rglob("data_lake"):
        if not path.is_dir():
            continue
        if allowed in path.parents or path == allowed:
            continue
        rel = str(path.relative_to(REPO_ROOT))
        if rel.startswith(("platform/tests/", "platform/verification/", ".venv/")):
            continue
        offenders.append(rel)
    assert offenders == []
