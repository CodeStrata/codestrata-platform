"""Architecture boundary for Community Cloud structured logging."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

import ast
from pathlib import Path

import yaml

from codestrata_platform.community_cloud_api import (
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_LOGGING_POLICY_URN,
    COMMUNITY_LOGGING_POLICY_VERSION,
    create_community_cloud_app,
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
    / "logging"
)


def test_logging_package_platform_only() -> None:
    assert (PKG / "logger.py").is_file()
    assert (PKG / "formatter.py").is_file()
    assert (PKG / "sanitization.py").is_file()
    assert list(ENGINE_SRC.rglob("*community_cloud_api*logging*")) == []


def test_engine_has_no_community_logging_tokens() -> None:
    forbidden = (
        "community-logging-policy",
        "CommunityCloudLogger",
        "CommunityLoggingPolicy",
        "community_cloud_api.logging",
        "COMMUNITY_LOGGING_POLICY_URN",
    )
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_engine_ast_no_community_logging_import() -> None:
    for path in ENGINE_SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "community_cloud_api.logging" not in node.module


def test_community_cli_unchanged() -> None:
    hits = []
    for path in ENGINE_CLI.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "community-logging-policy" in text or "CommunityCloudLogger" in text:
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []


def test_public_export_excludes_platform() -> None:
    manifest = yaml.safe_load(
        (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    assert "platform/" in forbidden


def test_production_routes_are_health_telemetry_and_assessment_metadata() -> None:
    registry = create_community_cloud_app(authentication_policy=disabled_authentication_policy()).state.community_cloud_route_registry
    assert {(r.method, r.path) for r in registry.list_routes()} >= {
        ("GET", "/health"),
        ("POST", "/ai-usage"),
        ("POST", "/assessment-metadata"),
        ("POST", "/cli-events"),
        ("POST", "/extension-events"),
        ("POST", "/telemetry"),
    }


def test_no_opentelemetry_or_shipping_packages() -> None:
    cloud_api = PKG.parent  # community_cloud_api
    assert PKG.is_dir()
    # Community Cloud telemetry package is allowed; standalone OpenTelemetry is not.
    assert (cloud_api / "telemetry").is_dir()
    platform_root = cloud_api.parent
    assert not (platform_root / "telemetry").exists()
    for name in ("opentelemetry", "auth", "rate_limit", "persistence"):
        assert not (platform_root / name).exists()
        assert not (cloud_api / name).exists()


def test_schema_and_logging_policy_versions() -> None:
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_LOGGING_POLICY_VERSION == "1.0"
    assert COMMUNITY_LOGGING_POLICY_URN == "community-logging-policy:1.0"
