"""Commercial boundary for OSS demonstration (Platform-only)."""

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
    / "oss_demonstration"
)


def test_package_exists_on_platform() -> None:
    assert (PKG / "builder.py").is_file()
    assert (PKG / "catalog.py").is_file()
    assert (REPO_ROOT / "platform" / "demo" / "catalog.json").is_file()


def test_engine_has_no_oss_demonstration_builder() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "build_oss_demonstration_report" not in text
        assert "generate_oss_demonstration_artifacts" not in text


def test_community_cli_has_no_oss_demo_command() -> None:
    cli = ENGINE_SRC / "codestrata" / "cli"
    hits = []
    for path in cli.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "oss-demonstration" in text or "build_oss_demonstration_report" in text:
            hits.append(str(path))
    assert hits == []


def test_engine_does_not_import_platform_oss_demonstration() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "intelligence_reporting.application.oss_demonstration" not in (
                    node.module
                )
