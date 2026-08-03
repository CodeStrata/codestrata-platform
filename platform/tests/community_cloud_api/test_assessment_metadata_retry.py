"""Assessment metadata retry / identity behavior."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.assessment_metadata.enums import (
    ASSESSMENT_METADATA_EVENT_TYPE,
)
from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.assessment_metadata.ports import (
    InMemoryAssessmentMetadataSink,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_ASSESSMENT_METADATA_IDENTITY_UNAVAILABLE,
    ERROR_ASSESSMENT_METADATA_RECORD_FAILED,
    ERROR_ASSESSMENT_METADATA_REJECTED,
    ERROR_ASSESSMENT_METADATA_SINK_UNAVAILABLE,
    ERROR_EVENT_IDENTITY_CONFLICT,
)
from codestrata_platform.community_cloud_api.event_identity import (
    EventIdentityScope,
    InMemoryEventIdentityStore,
    build_event_key,
    compute_payload_fingerprint,
)
from fastapi.testclient import TestClient

from .assessment_metadata_helpers import (
    configured_metadata_client,
    valid_assessment_metadata_body,
)


def test_exact_retry_and_conflict() -> None:
    client, sink, _, log_sink, _ = configured_metadata_client()
    first = client.post("/api/v1/assessment-metadata", json=valid_assessment_metadata_body())
    assert first.status_code == 202
    ref = first.json()["safe_event_reference"]
    second = client.post(
        "/api/v1/assessment-metadata", json=valid_assessment_metadata_body()
    )
    assert second.status_code == 200
    assert second.json()["status"] == "already_accepted"
    assert second.json()["safe_event_reference"] == ref
    assert len(sink.events) == 1
    assert any(e.get("event_type") == "assessment_metadata_retry" for e in log_sink.events())

    conflict_body = valid_assessment_metadata_body()
    conflict_body["assessment"] = {
        **conflict_body["assessment"],  # type: ignore[dict-item]
        "finding_count": 99,
    }
    conflict = client.post("/api/v1/assessment-metadata", json=conflict_body)
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == ERROR_EVENT_IDENTITY_CONFLICT
    assert "99" not in conflict.text
    assert "amd-test-0001" not in conflict.text
    assert len(sink.events) == 1


def test_fingerprint_and_event_type() -> None:
    model = AssessmentMetadataRequest.model_validate(valid_assessment_metadata_body())
    fp1 = compute_payload_fingerprint(model.fingerprint_payload())
    assert "request_id" not in model.fingerprint_payload()
    assert "event_id" in model.fingerprint_payload()
    scope = EventIdentityScope(
        api_version="v1",
        client_type="codestrata_cli",
        event_type=ASSESSMENT_METADATA_EVENT_TYPE,
        event_id="amd-test-0001",
    )
    assert build_event_key(scope) == build_event_key(scope)
    other = AssessmentMetadataRequest.model_validate(
        valid_assessment_metadata_body(event_id="amd-test-0002")
    )
    assert compute_payload_fingerprint(other.fingerprint_payload()) != fp1


def test_scope_distinct_by_client_and_installation() -> None:
    client, sink, _, _, _ = configured_metadata_client()
    assert (
        client.post("/api/v1/assessment-metadata", json=valid_assessment_metadata_body()).status_code
        == 202
    )
    other = valid_assessment_metadata_body()
    other["client"] = {
        "name": "vscode_extension",
        "version": "0.2.0",
        "platform": "darwin",
    }
    assert client.post("/api/v1/assessment-metadata", json=other).status_code == 202
    with_install = valid_assessment_metadata_body(installation_id="install-abcdef12")
    assert client.post("/api/v1/assessment-metadata", json=with_install).status_code == 202
    assert len(sink.events) == 3


def test_sink_recorder_failures() -> None:
    store = InMemoryEventIdentityStore()
    sink = InMemoryAssessmentMetadataSink()
    sink.reject_next = True
    client = TestClient(
        create_community_cloud_app(
            assessment_metadata_sink=sink,
            event_identity_lookup=store,
            event_identity_recorder=store,
                authentication_policy=disabled_authentication_policy(),
    )
    )
    rejected = client.post(
        "/api/v1/assessment-metadata", json=valid_assessment_metadata_body()
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == ERROR_ASSESSMENT_METADATA_REJECTED

    sink2 = InMemoryAssessmentMetadataSink()
    sink2.fail_next = True
    client2 = TestClient(
        create_community_cloud_app(
            assessment_metadata_sink=sink2,
            event_identity_lookup=store,
            event_identity_recorder=store,
                authentication_policy=disabled_authentication_policy(),
    )
    )
    boom = client2.post(
        "/api/v1/assessment-metadata", json=valid_assessment_metadata_body(event_id="amd-fail-0001")
    )
    assert boom.status_code == 503
    assert boom.json()["error"]["code"] == ERROR_ASSESSMENT_METADATA_SINK_UNAVAILABLE
    assert "simulated_metadata_sink_failure" not in boom.text

    class BoomRecorder:
        def record(self, identity: object) -> None:
            raise RuntimeError("recorder_boom")

    sink3 = InMemoryAssessmentMetadataSink()
    client3 = TestClient(
        create_community_cloud_app(
            assessment_metadata_sink=sink3,
            event_identity_lookup=InMemoryEventIdentityStore(),
            event_identity_recorder=BoomRecorder(),
                authentication_policy=disabled_authentication_policy(),
    )
    )
    rec = client3.post(
        "/api/v1/assessment-metadata",
        json=valid_assessment_metadata_body(event_id="amd-rec-0001"),
    )
    assert rec.status_code == 503
    assert rec.json()["error"]["code"] == ERROR_ASSESSMENT_METADATA_RECORD_FAILED
    assert len(sink3.events) == 1


def test_no_lookup_fail_closed_independent_of_telemetry() -> None:
    meta = InMemoryAssessmentMetadataSink()
    client = TestClient(create_community_cloud_app(assessment_metadata_sink=meta,
        authentication_policy=disabled_authentication_policy(),
    ))
    response = client.post(
        "/api/v1/assessment-metadata", json=valid_assessment_metadata_body()
    )
    assert response.status_code == 503
    assert (
        response.json()["error"]["code"] == ERROR_ASSESSMENT_METADATA_IDENTITY_UNAVAILABLE
    )
    assert meta.events == []
