"""Commercial boundary for website-safe EIR export (Platform-only)."""

from __future__ import annotations

import ast
from pathlib import Path

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.intelligence_reporting.application.website_export import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)


REPO_ROOT = Path(__file__).resolve().parents[5]
ENGINE_SRC = REPO_ROOT / "engine" / "src"
PKG = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "intelligence_reporting"
    / "application"
    / "website_export"
)
PRESENTATION = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "intelligence_reporting"
    / "presentation"
    / "static_html"
)


def test_package_exists_on_platform() -> None:
    assert (PKG / "builder.py").is_file()
    assert (PKG / "policy.py").is_file()
    assert (PKG / "projection.py").is_file()
    assert (PRESENTATION / "renderer.py").is_file()
    assert (
        REPO_ROOT
        / "platform"
        / "src"
        / "codestrata_platform"
        / "intelligence_reporting"
        / "infrastructure"
        / "static_export_writer.py"
    ).is_file()


def test_engine_has_no_eir_website_exporter() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "build_website_safe_export" not in text
        assert "WebsiteExportBuildPolicy" not in text
        assert "WebsiteSafeExportDocument" not in text


def test_community_cli_has_no_eir_export_command() -> None:
    cli = ENGINE_SRC / "codestrata" / "cli"
    hits = []
    for path in cli.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "website-safe" in text or "build_website_safe_export" in text:
            hits.append(str(path))
    assert hits == []


def test_engine_does_not_import_platform_website_export() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "intelligence_reporting.application.website_export" not in node.module
                assert "intelligence_reporting.presentation" not in node.module


def test_schema_constants_unchanged() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
