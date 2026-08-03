"""Commercial boundary for report quality (Platform-only)."""

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
    / "report_quality"
)


def test_package_exists_on_platform() -> None:
    assert (PKG / "builder.py").is_file()
    assert (PKG / "policy.py").is_file()
    assert (PKG / "confidence.py").is_file()
    assert (PKG / "limitations.py").is_file()


def test_engine_has_no_report_quality_builder() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "build_report_quality" not in text
        assert "ReportQualityPolicy" not in text
        assert "populate_report_quality" not in text


def test_community_cli_has_no_report_quality_command() -> None:
    cli = ENGINE_SRC / "codestrata" / "cli"
    hits = []
    for path in cli.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "report-quality" in text or "populate_report_quality" in text:
            hits.append(str(path))
    assert hits == []


def test_engine_does_not_import_platform_report_quality() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "intelligence_reporting.application.report_quality" not in node.module


def test_schema_constants_unchanged() -> None:
    from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
    from codestrata_platform.intelligence_reporting.domain.report import (
        ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
    )

    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
