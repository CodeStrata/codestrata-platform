"""Helpers shared by assessment metadata tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.assessment_metadata.ports import (
    InMemoryAssessmentMetadataSink,
)
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.logging.logger import (
    CommunityCloudLogger,
    MemoryLogSink,
)
from codestrata_platform.community_cloud_api.telemetry.ports import InMemoryTelemetryEventSink
from fastapi.testclient import TestClient


def valid_assessment_metadata_body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "1.0",
        "event_id": "amd-test-0001",
        "client": {
            "name": "codestrata_cli",
            "version": "0.2.0",
            "platform": "darwin",
        },
        "assessment": {
            "assessment_schema_version": "1.2",
            "assessment_status": "completed",
            "assessment_mode": "deterministic",
            "executed_heads": ["technology_inventory", "security"],
            "finding_count": 3,
            "recommendation_count": 2,
            "priority_action_count": 1,
            "roadmap_initiative_count": 0,
            "evidence_count": 4,
            "limitation_count": 1,
        },
        "repository": {
            "primary_language": "python",
            "language_count": 1,
            "dependency_ecosystem_count": 1,
            "file_count_bucket": "51_to_200",
            "source_file_count_bucket": "11_to_50",
            "test_file_count_bucket": "1_to_10",
            "repository_shape": "application",
            "has_tests": True,
            "has_build_files": True,
            "has_dependency_manifests": True,
        },
        "execution": {
            "duration_bucket": "10s_to_30s",
            "result": "succeeded",
            "ai_used": False,
            "offline_mode": True,
            "client_version": "0.2.0",
            "platform": "darwin",
        },
        "artifacts": {
            "report_json_generated": True,
            "findings_json_generated": True,
            "recommendations_json_generated": True,
            "html_report_generated": True,
            "artifact_count": 4,
        },
    }
    body.update(overrides)
    return body


def configured_metadata_client() -> tuple[
    TestClient,
    InMemoryAssessmentMetadataSink,
    InMemoryEventIdentityStore,
    MemoryLogSink,
    InMemoryTelemetryEventSink,
]:
    store = InMemoryEventIdentityStore()
    meta_sink = InMemoryAssessmentMetadataSink()
    tel_sink = InMemoryTelemetryEventSink()
    log_sink = MemoryLogSink()
    logger = CommunityCloudLogger.create(sink=log_sink)
    app = create_community_cloud_app(
        telemetry_sink=tel_sink,
        assessment_metadata_sink=meta_sink,
        event_identity_lookup=store,
        event_identity_recorder=store,
        logger=logger,
            authentication_policy=disabled_authentication_policy(),
    )
    return TestClient(app), meta_sink, store, log_sink, tel_sink
