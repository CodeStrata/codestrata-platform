"""SV.6 packaging / architecture boundary tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)

REPO = Path(__file__).resolve().parents[4]
PLATFORM = REPO / "platform"
PKG = PLATFORM / "src" / "codestrata_platform"
VERIFICATION = PLATFORM / "verification" / "engineering_intelligence"
ENGINE = REPO / "engine" / "src" / "codestrata"


def test_verification_outside_runtime_package() -> None:
    assert (VERIFICATION / "runner.py").is_file()
    assert (VERIFICATION / "README.md").is_file()
    assert not (PKG / "verification").exists()


def test_engine_has_no_eir_models() -> None:
    hits = []
    for path in ENGINE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "EngineeringIntelligenceReport" in text or "CrossRepositoryAggregation" in text:
            hits.append(str(path.relative_to(ENGINE)))
        if "codestrata_platform.intelligence_reporting" in text:
            hits.append(str(path.relative_to(ENGINE)))
    assert not hits, hits


def test_public_export_excludes_platform() -> None:
    manifest = yaml.safe_load((REPO / "public-export-manifest.yaml").read_text(encoding="utf-8"))
    blob = yaml.safe_dump(manifest)
    assert "platform/" in blob or "platform/**" in blob
    assert "codestrata_platform.intelligence_reporting" not in (
        (manifest.get("exports") or [{}])[0].get("include") or []
    )


def test_schema_constants_unchanged() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"


def test_no_second_repository_list() -> None:
    from verification.engineering_intelligence.contract import CATALOG_RELATIVE_PATH

    text = (VERIFICATION / "catalog.py").read_text(encoding="utf-8")
    assert "CATALOG_RELATIVE_PATH" in text or CATALOG_RELATIVE_PATH in text
    assert "github.com/ardalis" not in text
    assert CATALOG_RELATIVE_PATH == "validation/repository-catalog/catalog.json"
