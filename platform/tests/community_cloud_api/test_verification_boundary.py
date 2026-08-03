"""Slice 7.15 — Epic 7 final boundary verification (no product changes)."""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

from codestrata_platform.community_cloud_api.deployment import (
    create_production_foundation_app,
    load_deployment_settings,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_AUTHENTICATION_UNAVAILABLE,
)
from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform import __version__ as _platform_version
from codestrata_platform.community_cloud_api import COMMUNITY_CLOUD_API_SCHEMA_VERSION
from codestrata_platform.community_cloud_api.authentication import (
    COMMUNITY_AUTHENTICATION_POLICY_VERSION,
    COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION,
)
from codestrata_platform.community_cloud_api.rate_limiting import (
    COMMUNITY_RATE_LIMIT_POLICY_VERSION,
)
from codestrata_platform.intelligence_reporting.application.website_export import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)
from fastapi.testclient import TestClient

from .e2e_helpers import body_for
from .telemetry_helpers import valid_telemetry_body

_ = _platform_version

REPO_ROOT = Path(__file__).resolve().parents[3]
ENGINE_SRC = REPO_ROOT / "engine" / "src" / "codestrata"
ENGINE_CLI = ENGINE_SRC / "cli"
VSCODE = REPO_ROOT / "vscode-plugin"
CURSOR = REPO_ROOT / "cursor-plugin"
INFRA = REPO_ROOT / "infrastructure"
PKG = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "community_cloud_api"
)


def test_engine_imports_nothing_from_community_cloud() -> None:
    assert list(ENGINE_SRC.rglob("*community_cloud_api*")) == []
    for path in ENGINE_SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "community_cloud_api" not in node.module
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "community_cloud_api" not in alias.name


def test_community_cli_has_no_http_client_for_cloud() -> None:
    hits: list[str] = []
    for path in ENGINE_CLI.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        if any(
            needle in text
            for needle in (
                "community_cloud_api",
                "community-cloud",
                "/api/v1/telemetry",
                "/api/v1/health",
                "create_community_cloud_app",
            )
        ):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []


def test_vscode_and_cursor_extensions_unchanged() -> None:
    needles = (
        "/api/v1/telemetry",
        "/api/v1/assessment-metadata",
        "/api/v1/cli-events",
        "/api/v1/extension-events",
        "/api/v1/ai-usage",
        "community_cloud_api",
        "cscc_v1_",
    )
    for root in (VSCODE, CURSOR):
        if not root.exists():
            continue
        for path in list(root.rglob("*.ts")) + list(root.rglob("*.js")):
            text = path.read_text(encoding="utf-8")
            for needle in needles:
                assert needle not in text, f"{path}:{needle}"


def test_infrastructure_remains_separate_private_boundary() -> None:
    assert INFRA.is_dir()
    assert (INFRA / "modules" / "community-cloud-api").is_dir()
    assert (INFRA / "production").is_dir()
    # No application source under infrastructure except tests.
    for path in INFRA.rglob("*.py"):
        assert "tests" in path.parts
    # No OpenTofu resources that invent product sinks/data lake in this epic.
    blob = "\n".join(
        p.read_text(encoding="utf-8")
        for p in (INFRA / "modules" / "community-cloud-api").glob("*.tf")
    )
    assert 'resource "aws_s3_bucket"' not in blob
    assert 'resource "aws_sqs_queue"' not in blob


def test_public_export_excludes_platform_and_infrastructure() -> None:
    blob = (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    assert "platform/" in blob
    assert "infrastructure/" in blob
    manifest = yaml.safe_load(blob)
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    assert "platform/" in forbidden
    assert "infrastructure/" in forbidden


def test_deployment_adapter_still_fail_closed_for_ingestion() -> None:
    app = create_production_foundation_app(settings=load_deployment_settings({}))
    client = TestClient(app)
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    blocked = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert blocked.status_code == 503
    assert blocked.json()["error"]["code"] == ERROR_AUTHENTICATION_UNAVAILABLE
    assert app.state.community_cloud_route_registry.diagnostics().registered_route_count == 6


def test_schema_and_policy_versions_unchanged() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_AUTHENTICATION_POLICY_VERSION == "1.0"
    assert COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION == "1"
    assert COMMUNITY_RATE_LIMIT_POLICY_VERSION == "1.1"


def test_no_new_production_packages_for_epic8() -> None:
    for name in (
        "persistence",
        "queues",
        "workers",
        "analytics",
        "data_lake",
        "emitters",
        "auth",
    ):
        assert not (PKG / name).exists()
    assert (PKG / "deployment").is_dir()
    assert (PKG / "authentication").is_dir()


def test_body_helpers_cover_all_ingestion_kinds() -> None:
    for kind in (
        "telemetry",
        "assessment_metadata",
        "cli_events",
        "extension_events",
        "ai_usage",
    ):
        assert body_for(kind)["schema_version"] == "1.0"
