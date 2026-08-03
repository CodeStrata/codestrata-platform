"""Helpers for extension event tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.assessment_metadata.ports import (
    InMemoryAssessmentMetadataSink,
)
from codestrata_platform.community_cloud_api.cli_events.ports import InMemoryCliEventSink
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.extension_events.ports import (
    InMemoryExtensionEventSink,
)
from codestrata_platform.community_cloud_api.logging.logger import (
    CommunityCloudLogger,
    MemoryLogSink,
)
from codestrata_platform.community_cloud_api.telemetry.ports import InMemoryTelemetryEventSink
from fastapi.testclient import TestClient


def valid_extension_event_body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "1.0",
        "event_id": "ext-evt-0001",
        "client": {
            "name": "vscode_extension",
            "version": "0.2.0",
            "editor": "vscode",
            "editor_version": "1.85.0",
            "platform": "darwin",
        },
        "event": {
            "operation": "assess",
            "lifecycle": "completed",
            "result": "succeeded",
            "duration_bucket": "5s_to_30s",
        },
        "context": {
            "invocation_source": "command_palette",
            "user_initiated": True,
            "offline_mode": True,
            "ai_requested": False,
            "selected_assessment_heads": ["security", "technology_inventory"],
            "report_surface": "editor_tab",
            "workspace_state": "folder_open",
        },
    }
    body.update(overrides)
    return body


def configured_extension_client() -> tuple[
    TestClient,
    InMemoryExtensionEventSink,
    InMemoryEventIdentityStore,
    MemoryLogSink,
    InMemoryTelemetryEventSink,
    InMemoryAssessmentMetadataSink,
    InMemoryCliEventSink,
]:
    store = InMemoryEventIdentityStore()
    ext_sink = InMemoryExtensionEventSink()
    tel_sink = InMemoryTelemetryEventSink()
    meta_sink = InMemoryAssessmentMetadataSink()
    cli_sink = InMemoryCliEventSink()
    log_sink = MemoryLogSink()
    logger = CommunityCloudLogger.create(sink=log_sink)
    app = create_community_cloud_app(
        telemetry_sink=tel_sink,
        assessment_metadata_sink=meta_sink,
        cli_event_sink=cli_sink,
        extension_event_sink=ext_sink,
        event_identity_lookup=store,
        event_identity_recorder=store,
        logger=logger,
            authentication_policy=disabled_authentication_policy(),
    )
    return TestClient(app), ext_sink, store, log_sink, tel_sink, meta_sink, cli_sink
