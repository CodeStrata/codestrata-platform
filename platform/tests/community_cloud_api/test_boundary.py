"""Architecture boundary: Community Cloud API is Platform-only."""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

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


def test_package_exists_on_platform() -> None:
    assert (PKG / "app.py").is_file()
    assert (PKG / "registry.py").is_file()
    assert (PKG / "errors.py").is_file()
    assert (PKG / "serialization.py").is_file()
    assert (PKG / "health" / "handler.py").is_file()
    assert (PKG / "health" / "routes.py").is_file()
    assert (PKG / "validation" / "validator.py").is_file()
    assert (PKG / "validation" / "schema.py").is_file()
    assert (PKG / "payload_limits" / "validation.py").is_file()
    assert (PKG / "payload_limits" / "policy.py").is_file()
    assert (PKG / "logging" / "logger.py").is_file()
    assert (PKG / "logging" / "formatter.py").is_file()
    assert (PKG / "event_identity" / "models.py").is_file()
    assert (PKG / "event_identity" / "fingerprint.py").is_file()
    assert (PKG / "telemetry" / "service.py").is_file()
    assert (PKG / "telemetry" / "routes.py").is_file()
    assert (PKG / "assessment_metadata" / "service.py").is_file()
    assert (PKG / "assessment_metadata" / "routes.py").is_file()
    assert (PKG / "cli_events" / "service.py").is_file()
    assert (PKG / "cli_events" / "routes.py").is_file()
    assert (PKG / "extension_events" / "service.py").is_file()
    assert (PKG / "extension_events" / "routes.py").is_file()
    assert (PKG / "ai_usage" / "service.py").is_file()
    assert (PKG / "ai_usage" / "routes.py").is_file()


def test_engine_has_no_community_cloud_api_package() -> None:
    assert list(ENGINE_SRC.rglob("*community_cloud_api*")) == []
    assert list(ENGINE_SRC.rglob("*community_cloud*health*")) == []


def test_engine_contains_no_community_cloud_tokens() -> None:
    forbidden = (
        "create_community_cloud_app",
        "CommunityCloud",
        "community_cloud_api",
        "CommunityHealthResponse",
        "RouteRegistry.foundation_v1",
        "/api/v1/health",
        "/api/v1/telemetry",
        "/api/v1/assessment-metadata",
        "/api/v1/cli-events",
        "/api/v1/extension-events",
        "/api/v1/ai-usage",
    )
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        # ACTIVE_CURRENT_PLATFORM_CONTRACT: Engine telemetry wire models
        # (CommunityCloudTelemetryWireRequest) are shipped client contracts,
        # not the Platform community_cloud_api package.
        if "community_cloud" in path.parts or path.name in {
            "transport.py",
            "transport_models.py",
            "transport_mapping.py",
        }:
            continue
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_engine_ast_does_not_import_community_cloud_api() -> None:
    for path in ENGINE_SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "community_cloud_api" not in node.module
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "community_cloud_api" not in alias.name


def test_community_cli_has_no_cloud_api_commands() -> None:
    hits: list[str] = []
    for path in ENGINE_CLI.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        if (
            "community-cloud" in text
            or "community_cloud_api" in text
            or "api/v1/health" in text
        ):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []


def test_no_auth_or_persistence_packages_added() -> None:
    # Slice 7.7–7.13 packages are intentional and Platform-owned.
    assert (PKG / "telemetry").is_dir()
    assert (PKG / "assessment_metadata").is_dir()
    assert (PKG / "cli_events").is_dir()
    assert (PKG / "extension_events").is_dir()
    assert (PKG / "ai_usage").is_dir()
    assert (PKG / "rate_limiting").is_dir()
    assert (PKG / "authentication").is_dir()
    assert not (PKG / "auth").exists()
    assert not (PKG / "persistence").exists()
    assert not (PKG / "rate_limit").exists()
    # Slice 7.5 structured logging foundation is intentional.
    assert (PKG / "logging").is_dir()
    assert (PKG / "payload_limits").is_dir()
    assert (PKG / "event_identity").is_dir()


def test_public_export_excludes_platform_package() -> None:
    blob = (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    assert "platform/**" in blob
    manifest = yaml.safe_load(blob)
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    assert "platform/" in forbidden


def test_intelligence_reporting_packages_untouched_by_health() -> None:
    # Health must not live under commercial IR packages.
    ir = (
        REPO_ROOT
        / "platform"
        / "src"
        / "codestrata_platform"
        / "intelligence_reporting"
    )
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in ir.rglob("*.py")
        if "community_cloud_api" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
