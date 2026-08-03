"""Helpers for AI usage tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.ai_usage.ports import InMemoryAiUsageSink
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


def valid_ai_usage_body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "1.0",
        "event_id": "ai-usage-0001",
        "client": {
            "name": "codestrata_cli",
            "version": "0.2.0",
            "platform": "darwin",
        },
        "usage": {
            "capability": "modernization_advisor",
            "execution_mode": "deterministic_with_ai",
            "provider_ownership": "customer_managed",
            "provider_family": "openai",
            "model_family": "gpt_family",
            "outcome": "succeeded",
            "duration_bucket": "1s_to_5s",
            "input_token_bucket": "1k_to_4k",
            "output_token_bucket": "1_to_1k",
            "total_token_bucket": "1k_to_4k",
            "tool_usage": "not_used",
            "rag_usage": "not_used",
            "graph_usage": "not_used",
        },
        "context": {
            "assessment_head": "modernization",
            "invocation_source": "cli",
            "offline_mode": False,
            "user_initiated": True,
            "data_scope": "aggregate_assessment_metadata",
            "output_usage": "included_in_report",
        },
    }
    body.update(overrides)
    return body


def configured_ai_usage_client() -> tuple[
    TestClient,
    InMemoryAiUsageSink,
    InMemoryEventIdentityStore,
    MemoryLogSink,
    InMemoryTelemetryEventSink,
    InMemoryAssessmentMetadataSink,
    InMemoryCliEventSink,
    InMemoryExtensionEventSink,
]:
    store = InMemoryEventIdentityStore()
    ai_sink = InMemoryAiUsageSink()
    tel_sink = InMemoryTelemetryEventSink()
    meta_sink = InMemoryAssessmentMetadataSink()
    cli_sink = InMemoryCliEventSink()
    ext_sink = InMemoryExtensionEventSink()
    log_sink = MemoryLogSink()
    logger = CommunityCloudLogger.create(sink=log_sink)
    app = create_community_cloud_app(
        telemetry_sink=tel_sink,
        assessment_metadata_sink=meta_sink,
        cli_event_sink=cli_sink,
        extension_event_sink=ext_sink,
        ai_usage_sink=ai_sink,
        event_identity_lookup=store,
        event_identity_recorder=store,
        logger=logger,
            authentication_policy=disabled_authentication_policy(),
    )
    return (
        TestClient(app),
        ai_sink,
        store,
        log_sink,
        tel_sink,
        meta_sink,
        cli_sink,
        ext_sink,
    )
