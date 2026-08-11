"""Telemetry Platform-only boundary and schema constant guards."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from pathlib import Path

import yaml

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.community_cloud_api import (
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_EVENT_IDENTITY_POLICY_VERSION,
    COMMUNITY_LOGGING_POLICY_VERSION,
    COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION,
    COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION,
    COMMUNITY_TELEMETRY_POLICY_VERSION,
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
    create_community_cloud_app,
)
from codestrata_platform.community_cloud_api.telemetry import (
    COMMUNITY_TELEMETRY_POLICY_URN,
)
from codestrata_platform.intelligence_reporting.application.website_export import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
ENGINE_SRC = REPO_ROOT / "engine" / "src" / "codestrata"
PKG = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "community_cloud_api"
)


def test_telemetry_package_exists_only_on_platform() -> None:
    assert (PKG / "telemetry" / "service.py").is_file()
    assert (PKG / "telemetry" / "routes.py").is_file()
    assert list(ENGINE_SRC.rglob("*community_cloud_api*telemetry*")) == []
    assert not (ENGINE_SRC / "community_cloud_api").exists()


def test_engine_has_no_post_telemetry_endpoint() -> None:
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "POST /api/v1/telemetry" not in text
        assert "create_community_cloud_app" not in text


def test_no_production_persistence_queue_auth() -> None:
    root = PKG
    for name in ("persistence", "queues", "workers", "auth", "rate_limit"):
        assert not (root / name).exists()
    assert (root / "telemetry").is_dir()
    assert (root / "event_identity").is_dir()


def test_production_routes_only_health_telemetry_and_assessment_metadata() -> None:
    paths = {
        (r.method, r.path)
        for r in create_community_cloud_app(authentication_policy=disabled_authentication_policy()).state.community_cloud_route_registry.list_routes()
    }
    assert paths >= {("GET", "/health"), ("POST", "/ai-usage"), ("POST", "/assessment-metadata"), ("POST", "/cli-events"), ("POST", "/extension-events"), ("POST", "/telemetry")}
    # No assessment / CLI / extension / AI aliases.
    for path in ("/events", "/track", "/usage", "/telemetry/batch", "/assessment"):
        assert ("POST", path) not in paths


def test_public_export_excludes_platform() -> None:
    manifest = yaml.safe_load(
        (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    assert "platform/" in forbidden


def test_schema_constants_unchanged() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION == "1.0"
    assert COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION == "1.0"
    assert COMMUNITY_LOGGING_POLICY_VERSION == "1.0"
    assert COMMUNITY_EVENT_IDENTITY_POLICY_VERSION == "1.0"
    assert COMMUNITY_TELEMETRY_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_TELEMETRY_POLICY_VERSION == "1.0"
    assert COMMUNITY_TELEMETRY_POLICY_URN == "community-telemetry-policy:1.0"
