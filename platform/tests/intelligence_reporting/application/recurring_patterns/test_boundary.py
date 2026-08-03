"""Boundary tests for recurring patterns."""

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
    / "recurring_patterns"
)


def test_package_exists_on_platform() -> None:
    assert (PKG / "builder.py").is_file()


def test_engine_has_no_recurring_pattern_builder() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "build_recurring_patterns" not in text
        assert "RecurringPatternPolicy" not in text


def test_community_cli_has_no_recurring_patterns_command() -> None:
    cli = ENGINE_SRC / "codestrata" / "cli"
    hits = []
    for path in cli.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "recurring-patterns" in text or "build_recurring_patterns" in text:
            hits.append(str(path))
    assert hits == []


def test_engine_does_not_import_platform_recurring_patterns() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "intelligence_reporting.application.recurring_patterns" not in (
                    node.module
                )
