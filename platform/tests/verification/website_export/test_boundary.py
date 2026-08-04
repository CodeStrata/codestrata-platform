"""SV.8 packaging / architecture boundary tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.intelligence_reporting.application.website_export import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)

REPO = Path(__file__).resolve().parents[4]
PLATFORM = REPO / "platform"
PKG = PLATFORM / "src" / "codestrata_platform"
VERIFICATION = PLATFORM / "verification" / "website_export"
ENGINE = REPO / "engine" / "src" / "codestrata"


def test_verification_outside_runtime_package() -> None:
    assert (VERIFICATION / "runner.py").is_file()
    assert (VERIFICATION / "README.md").is_file()
    assert not (PKG / "verification").exists()


def test_engine_does_not_import_website_export() -> None:
    hits = []
    for path in ENGINE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "codestrata_platform.intelligence_reporting.application.website_export" in text:
            hits.append(str(path.relative_to(ENGINE)))
        if "WebsiteSafeExportDocument" in text:
            hits.append(str(path.relative_to(ENGINE)))
    assert not hits, hits


def test_public_export_excludes_platform() -> None:
    manifest = yaml.safe_load((REPO / "public-export-manifest.yaml").read_text(encoding="utf-8"))
    blob = yaml.safe_dump(manifest)
    assert "platform/" in blob or "platform/**" in blob


def test_schema_constants_unchanged() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"


def test_no_sv9_started_here() -> None:
    text = (VERIFICATION / "README.md").read_text(encoding="utf-8")
    assert "SV.9" in text
    assert "not started" in text.lower()
