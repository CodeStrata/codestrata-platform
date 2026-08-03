"""Aggregation package commercial boundary tests."""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
ENGINE_SRC = REPO_ROOT / "engine" / "src"
AGG_PKG = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "intelligence_reporting"
    / "application"
    / "aggregation"
)


def test_aggregation_package_exists_on_platform() -> None:
    assert (AGG_PKG / "aggregate_dataset.py").is_file()
    assert (AGG_PKG / "models.py").is_file()


def test_engine_has_no_cross_repository_aggregation() -> None:
    hits = list((ENGINE_SRC / "codestrata").rglob("*cross_repository*"))
    assert hits == []
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "aggregate_intelligence_dataset" not in text
        assert "CrossRepositoryAggregation" not in text


def test_community_cli_has_no_aggregation_command() -> None:
    cli = ENGINE_SRC / "codestrata" / "cli"
    hits = []
    for path in cli.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "aggregate-intelligence" in text or "cross-repository-aggregation" in text:
            hits.append(str(path))
    assert hits == []


def test_engine_does_not_import_aggregation_package() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "intelligence_reporting.application.aggregation" not in node.module


def test_public_export_excludes_platform() -> None:
    blob = (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    assert "platform/**" in blob
