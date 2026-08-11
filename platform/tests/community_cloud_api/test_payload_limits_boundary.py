"""Architecture boundary for Community Cloud payload limits."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

import ast
from pathlib import Path

import yaml

from codestrata_platform.community_cloud_api import (
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION,
    PAYLOAD_LIMIT_POLICY_URN,
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
    / "payload_limits"
)


def test_payload_limits_package_platform_only() -> None:
    assert (PKG / "models.py").is_file()
    assert (PKG / "middleware.py").is_file()
    assert list(ENGINE_SRC.rglob("*payload_limits*")) == []


def test_engine_has_no_community_cloud_payload_limit_tokens() -> None:
    # Commercial Engine client may mention generic payload_too_large; Community
    # Cloud policy/package tokens must remain Platform-only.
    forbidden = (
        "payload-limit-policy",
        "PayloadLimitPolicy",
        "enforce_payload_limits",
        "community_cloud_api.payload_limits",
        "PAYLOAD_LIMIT_POLICY_URN",
    )
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_engine_ast_no_payload_limits_import() -> None:
    for path in ENGINE_SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "payload_limits" not in node.module


def test_community_cli_unchanged() -> None:
    hits = []
    for path in ENGINE_CLI.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "payload-limit-policy" in text or "enforce_payload_limits" in text:
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


def test_schema_and_policy_versions() -> None:
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION == "1.0"
    assert PAYLOAD_LIMIT_POLICY_URN == "payload-limit-policy:1.0"
