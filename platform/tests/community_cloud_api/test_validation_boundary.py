"""Architecture boundary for Community Cloud request validation."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

import ast
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.community_cloud_api import (
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION,
    create_community_cloud_app,
)
from codestrata_platform.intelligence_reporting.application.website_export import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
ENGINE_SRC = REPO_ROOT / "engine" / "src" / "codestrata"
ENGINE_CLI = ENGINE_SRC / "cli"
PKG = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "community_cloud_api"
)
VALIDATION = PKG / "validation"


def test_validation_package_exists_on_platform_only() -> None:
    assert (VALIDATION / "validator.py").is_file()
    assert (VALIDATION / "schema.py").is_file()
    assert (VALIDATION / "sanitization.py").is_file()
    assert list(ENGINE_SRC.rglob("*community_cloud_api*")) == []
    assert list(ENGINE_SRC.rglob("*request_validation*")) == []


def test_engine_has_no_validation_tokens() -> None:
    forbidden = (
        "CommunityApiRequestModel",
        "validate_request_body",
        "RequestSchemaDescriptor",
        "COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION",
        "community.test.validation-envelope",
    )
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_engine_ast_does_not_import_validation() -> None:
    for path in ENGINE_SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "community_cloud_api.validation" not in node.module
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "community_cloud_api.validation" not in alias.name


def test_community_cli_unchanged() -> None:
    hits: list[str] = []
    for path in ENGINE_CLI.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        if "validation-envelope" in text or "request_schema" in text:
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []


def test_no_auth_rate_limit_persistence() -> None:
    for name in ("auth", "rate_limit", "persistence", "queues"):
        assert not (PKG / name).exists()
    # Slice 7.4/7.5/7.7/7.8/7.9 packages are intentional and Platform-owned.
    assert (PKG / "payload_limits").is_dir()
    assert (PKG / "logging").is_dir()
    assert (PKG / "telemetry").is_dir()
    assert (PKG / "assessment_metadata").is_dir()
    assert (PKG / "cli_events").is_dir()
    assert (PKG / "extension_events").is_dir()
    assert (PKG / "ai_usage").is_dir()


def test_public_export_excludes_platform() -> None:
    manifest = yaml.safe_load(
        (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    assert "platform/" in forbidden


def test_production_routes_are_health_telemetry_and_assessment_metadata() -> None:
    app = create_community_cloud_app(authentication_policy=disabled_authentication_policy())
    registry = app.state.community_cloud_route_registry
    paths = {(item.method, item.path) for item in registry.list_routes()}
    assert paths >= {("GET", "/health"), ("POST", "/ai-usage"), ("POST", "/assessment-metadata"), ("POST", "/cli-events"), ("POST", "/extension-events"), ("POST", "/telemetry")}
    assert app.docs_url is None
    assert app.openapi_url is None


def test_schema_constants_unchanged() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION == "1.0"


def test_commercial_platform_api_still_has_root_health() -> None:
    # Unrelated commercial API surface remains distinct.
    from codestrata_platform.api import create_app

    commercial = TestClient(create_app(use_memory=True))
    assert commercial.get("/health").status_code == 200
