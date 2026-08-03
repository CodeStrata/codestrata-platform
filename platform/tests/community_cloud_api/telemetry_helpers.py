"""Helpers shared by telemetry ingestion tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.logging.logger import (
    CommunityCloudLogger,
    MemoryLogSink,
)
from codestrata_platform.community_cloud_api.telemetry.ports import InMemoryTelemetryEventSink
from fastapi.testclient import TestClient


def valid_telemetry_body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "1.0",
        "event_id": "evt-test-0001",
        "event_type": "application_started",
        "client": {
            "name": "codestrata_cli",
            "version": "0.2.0",
            "platform": "darwin",
        },
    }
    body.update(overrides)
    return body


def configured_client() -> tuple[TestClient, InMemoryTelemetryEventSink, InMemoryEventIdentityStore, MemoryLogSink]:
    store = InMemoryEventIdentityStore()
    sink = InMemoryTelemetryEventSink()
    log_sink = MemoryLogSink()
    logger = CommunityCloudLogger.create(sink=log_sink)
    app = create_community_cloud_app(
        telemetry_sink=sink,
        event_identity_lookup=store,
        event_identity_recorder=store,
        logger=logger,
            authentication_policy=disabled_authentication_policy(),
    )
    return TestClient(app), sink, store, log_sink
