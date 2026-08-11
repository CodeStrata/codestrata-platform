"""SV.9 packaging / architecture boundary tests."""

from __future__ import annotations

from pathlib import Path

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_AUTHENTICATION_POLICY_VERSION,
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_RATE_LIMIT_POLICY_VERSION,
)
from codestrata_platform.intelligence_reporting.application.website_export import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)

REPO = Path(__file__).resolve().parents[3]
INFRA = REPO / "infrastructure"
VERIFICATION = INFRA / "verification"
ENGINE = REPO / "engine" / "src" / "codestrata"


def test_verification_under_infrastructure() -> None:
    assert (VERIFICATION / "runner.py").is_file()
    assert (VERIFICATION / "README.md").is_file()


def test_no_sv10_started() -> None:
    text = (VERIFICATION / "README.md").read_text(encoding="utf-8")
    assert "SV.10" in text
    assert "not started" in text.lower()


def test_public_export_excludes_infrastructure() -> None:
    manifest = (REPO / "public-export-manifest.yaml").read_text(encoding="utf-8")
    assert "infrastructure/" in manifest or "infrastructure/**" in manifest


def test_engine_has_no_infrastructure_imports() -> None:
    hits = []
    for path in ENGINE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "infrastructure.verification" in text or "infrastructure/modules" in text:
            hits.append(str(path.relative_to(ENGINE)))
    assert not hits, hits


def test_schema_constants_unchanged() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_AUTHENTICATION_POLICY_VERSION == "1.0"
    assert COMMUNITY_RATE_LIMIT_POLICY_VERSION == "1.1"


def test_community_data_lake_module_present_with_fail_closed_default() -> None:
    module = INFRA / "modules" / "community-data-lake"
    assert module.is_dir()
    assert not (INFRA / "modules" / "data-lake").exists()
    variables = (module / "variables.tf").read_text(encoding="utf-8")
    assert "enable_ingestion_wire" in variables
    assert "default     = false" in variables
    api_iam = (INFRA / "modules" / "community-cloud-api" / "iam.tf").read_text(
        encoding="utf-8"
    )
    assert "community-data-lake" not in api_iam
    assert "community_data_lake" not in api_iam
