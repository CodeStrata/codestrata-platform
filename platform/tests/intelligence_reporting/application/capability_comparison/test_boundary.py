"""Boundary tests for capability comparison."""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
ENGINE_SRC = REPO_ROOT / "engine" / "src"
PKG = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "intelligence_reporting"
    / "application"
    / "capability_comparison"
)


def test_package_exists_on_platform() -> None:
    assert (PKG / "builder.py").is_file()


def test_engine_has_no_capability_comparison_builder() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "build_capability_comparisons" not in text
        assert "CapabilityComparisonPolicy" not in text


def test_community_cli_has_no_capability_comparison_command() -> None:
    cli = ENGINE_SRC / "codestrata" / "cli"
    hits = []
    for path in cli.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "capability-comparison" in text or "build_capability_comparisons" in text:
            hits.append(str(path))
    assert hits == []


def test_engine_does_not_import_platform_capability_comparison() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "intelligence_reporting.application.capability_comparison" not in (
                    node.module
                )
