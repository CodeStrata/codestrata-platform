"""Authentication logging and boundary tests."""

from __future__ import annotations

from pathlib import Path

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_AUTHENTICATION_POLICY_VERSION,
    COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION,
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_RATE_LIMIT_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.logging.logger import (
    CommunityCloudLogger,
    MemoryLogSink,
)
from codestrata_platform.community_cloud_api.registry import RouteRegistry
from codestrata_platform.community_cloud_api.telemetry.ports import InMemoryTelemetryEventSink
from fastapi.testclient import TestClient

from .auth_test_support import TEST_CLI_TOKEN, auth_headers, build_test_verifier
from .telemetry_helpers import valid_telemetry_body

PKG = Path(__file__).resolve().parents[2] / "src" / "codestrata_platform" / "community_cloud_api"


def test_authentication_logging_safe() -> None:
    sink = InMemoryTelemetryEventSink()
    store = InMemoryEventIdentityStore()
    log_sink = MemoryLogSink()
    logger = CommunityCloudLogger.create(sink=log_sink)
    app = create_community_cloud_app(
        telemetry_sink=sink,
        event_identity_lookup=store,
        event_identity_recorder=store,
        credential_verifier=build_test_verifier(),
        logger=logger,
    )
    client = TestClient(app)
    assert (
        client.post(
            "/api/v1/telemetry",
            json=valid_telemetry_body(),
            headers=auth_headers(TEST_CLI_TOKEN),
        ).status_code
        == 202
    )
    assert client.post("/api/v1/telemetry", json=valid_telemetry_body()).status_code == 401
    blob = str(log_sink.events())
    assert TEST_CLI_TOKEN not in blob
    assert "Authorization" not in blob
    assert "cred:" not in blob
    types = {item["event_type"] for item in log_sink.events()}
    assert "authentication_succeeded" in types
    assert "authentication_failed" in types


def test_authentication_boundary_platform_only() -> None:
    assert (PKG / "authentication").is_dir()
    assert not (PKG / "auth").exists()
    assert not (PKG / "oauth").exists()
    assert not (PKG / "sessions").exists()
    assert len(RouteRegistry.foundation_v1().list_routes()) == 6
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_AUTHENTICATION_POLICY_VERSION == "1.0"
    assert COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION == "1"
    assert COMMUNITY_RATE_LIMIT_POLICY_VERSION == "1.1"
