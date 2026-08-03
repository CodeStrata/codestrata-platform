"""Commercial ingestion boundary tests."""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
ENGINE_SRC = REPO_ROOT / "engine" / "src"
PLATFORM_APP = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "intelligence_reporting"
    / "application"
)


def test_platform_ingestion_package_exists() -> None:
    assert (PLATFORM_APP / "ingestion.py").is_file()
    assert (PLATFORM_APP / "dataset_builder.py").is_file()


def test_engine_has_no_dataset_builder() -> None:
    hits = list((ENGINE_SRC / "codestrata").rglob("*dataset_builder*"))
    assert hits == []
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "ingest_assessment_dataset" not in text
        assert "IntelligenceDatasetSelectionPolicy" not in text


def test_community_cli_has_no_dataset_ingest_command() -> None:
    cli = ENGINE_SRC / "codestrata" / "cli"
    hits: list[str] = []
    for path in cli.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "intelligence-dataset" in text or "ingest_assessment_dataset" in text:
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []


def test_engine_reporting_does_not_import_platform_ingestion() -> None:
    reporting = ENGINE_SRC / "codestrata" / "reporting"
    for path in reporting.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(
                    "codestrata_platform.intelligence_reporting"
                )


def test_public_export_excludes_platform() -> None:
    blob = (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    assert "platform/**" in blob
