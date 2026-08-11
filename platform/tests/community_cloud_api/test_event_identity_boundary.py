"""Boundary and logging/health regression for event identity."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

import ast
import json
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.community_cloud_api import (
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_EVENT_IDENTITY_POLICY_VERSION,
    COMMUNITY_LOGGING_POLICY_VERSION,
    COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION,
    COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION,
    CommunityCloudLogger,
    create_community_cloud_app,
)
from codestrata_platform.community_cloud_api.logging import (
    LogEventType,
    MemoryLogSink,
    SequenceClock,
    SequenceRequestIdFactory,
)
from codestrata_platform.community_cloud_api.logging.context import create_logging_context
from codestrata_platform.community_cloud_api.logging.sanitization import (
    assert_safe_event_log_fields,
    ensure_no_payload_fields,
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
    / "event_identity"
)


def test_event_identity_platform_only() -> None:
    assert (PKG / "models.py").is_file()
    assert (PKG / "fingerprint.py").is_file()
    assert list(ENGINE_SRC.rglob("*community_cloud_api*event_identity*")) == []


def test_engine_has_no_community_event_identity_tokens() -> None:
    forbidden = (
        "community-event-identity-policy",
        "CommunityEventIdentityPolicy",
        "community_cloud_api.event_identity",
        "build_safe_event_reference",
        "classify_retry",
    )
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_engine_ast_no_event_identity_import() -> None:
    for path in ENGINE_SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "community_cloud_api.event_identity" not in (node.module or "")


def test_community_cli_unchanged() -> None:
    hits = []
    for path in ENGINE_CLI.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "community-event-identity-policy" in text or "safe_event_reference" in text:
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


def test_no_persistence_queue_auth_packages() -> None:
    root = PKG.parent  # community_cloud_api
    for name in ("auth", "rate_limit", "persistence", "queues", "workers"):
        assert not (root / name).exists()
    assert PKG.is_dir()
    assert (root / "telemetry").is_dir()
    assert (root / "event_identity").is_dir()


def test_schema_constants_unchanged() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION == "1.0"
    assert COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION == "1.0"
    assert COMMUNITY_LOGGING_POLICY_VERSION == "1.0"
    assert COMMUNITY_EVENT_IDENTITY_POLICY_VERSION == "1.0"


def test_logging_safe_event_fields_only() -> None:
    cleaned = ensure_no_payload_fields(
        {
            "event_id": "raw",
            "payload_fingerprint": "fp:abc",
            "installation_id": "inst",
            "safe_event_reference": "evt-aaaaaaaaaaaa",
        }
    )
    assert "event_id" not in cleaned
    assert "payload_fingerprint" not in cleaned
    assert "installation_id" not in cleaned
    allowed = assert_safe_event_log_fields(
        {
            "safe_event_reference": "evt-aaaaaaaaaaaa",
            "retry_status": "exact_retry",
            "source_event_type": "cli.started",
            "identity_policy_version": "1.0",
            "event_id": "should-drop",
        }
    )
    assert set(allowed) == {
        "safe_event_reference",
        "retry_status",
        "source_event_type",
        "identity_policy_version",
    }

    sink = MemoryLogSink()
    logger = CommunityCloudLogger.create(
        sink=sink,
        clock_ms=SequenceClock(),
        request_id_factory=SequenceRequestIdFactory(),
    )
    ctx = create_logging_context(
        policy=logger.policy,
        api_version="v1",
        method="POST",
        route="/api/v1/_test",
        client_request_id=None,
        clock_ms=logger.clock_ms,
        request_id_factory=logger.request_id_factory,
    )
    logger.emit(
        LogEventType.REQUEST_COMPLETED,
        context=ctx,
        status_code=200,
        duration_ms=1,
        safe_event_fields=allowed,
    )
    blob = json.dumps(sink.events())
    assert "evt-aaaaaaaaaaaa" in blob
    assert "should-drop" not in blob
    assert "fp:abc" not in blob


def test_health_logging_and_body_unchanged() -> None:
    sink = MemoryLogSink()
    logger = CommunityCloudLogger.create(
        sink=sink,
        clock_ms=SequenceClock(start_ms=1000, step_ms=5),
        request_id_factory=SequenceRequestIdFactory(prefix="log"),
    )
    client = TestClient(create_community_cloud_app(logger=logger,
        authentication_policy=disabled_authentication_policy(),
    ))
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "event_id" not in body
    assert "request_id" not in body
    types = [item["event_type"] for item in sink.events()]
    assert types == [
        "request_received",
        "rate_limit_allowed",
        "health_checked",
        "request_completed",
    ]
