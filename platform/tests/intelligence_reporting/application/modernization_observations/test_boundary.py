"""Boundary tests for modernization observations."""

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
    / "modernization_observations"
)


def test_package_exists_on_platform() -> None:
    assert (PKG / "builder.py").is_file()


def test_engine_has_no_modernization_observation_builder() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "build_modernization_observations" not in text
        assert "ModernizationObservationPolicy" not in text


def test_community_cli_has_no_modernization_observation_command() -> None:
    cli = ENGINE_SRC / "codestrata" / "cli"
    hits = []
    for path in cli.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "modernization-observations" in text or "build_modernization_observations" in text:
            hits.append(str(path))
    assert hits == []


def test_engine_does_not_import_platform_modernization_observations() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert (
                    "intelligence_reporting.application.modernization_observations"
                    not in node.module
                )
