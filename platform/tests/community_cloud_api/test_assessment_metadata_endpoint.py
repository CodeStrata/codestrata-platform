"""Assessment metadata endpoint tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.assessment_metadata.enums import (
    AssessmentMetadataIngestionStatus,
)
from codestrata_platform.community_cloud_api.assessment_metadata.ports import (
    UnavailableAssessmentMetadataSink,
)
from codestrata_platform.community_cloud_api.assessment_metadata.responses import (
    AssessmentMetadataResponse,
)
from codestrata_platform.community_cloud_api.assessment_metadata.routes import (
    ASSESSMENT_METADATA_ROUTE_NAME,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_ASSESSMENT_METADATA_IDENTITY_UNAVAILABLE,
    ERROR_ASSESSMENT_METADATA_SINK_UNAVAILABLE,
    ERROR_BODY_REQUIRED,
    ERROR_MALFORMED_JSON,
    ERROR_METHOD_NOT_ALLOWED,
    ERROR_UNSUPPORTED_ASSESSMENT_METADATA_SCHEMA,
    ERROR_UNSUPPORTED_MEDIA_TYPE,
)
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.registry import RouteRegistry
from codestrata_platform.community_cloud_api.serialization import dumps_stable
from fastapi.testclient import TestClient

from .assessment_metadata_helpers import (
    configured_metadata_client,
    valid_assessment_metadata_body,
)


def test_route_registered() -> None:
    registry = RouteRegistry.foundation_v1()
    spec = registry.get(version="v1", method="POST", path="/assessment-metadata")
    assert spec is not None
    assert spec.name == ASSESSMENT_METADATA_ROUTE_NAME
    assert registry.get_handler(spec) is not None


def test_get_body_media_malformed_schema() -> None:
    client, *_ = configured_metadata_client()
    assert client.get("/api/v1/assessment-metadata").status_code == 405
    assert (
        client.get("/api/v1/assessment-metadata").json()["error"]["code"]
        == ERROR_METHOD_NOT_ALLOWED
    )
    assert client.post("/api/v1/assessment-metadata").json()["error"]["code"] == ERROR_BODY_REQUIRED
    media = client.post(
        "/api/v1/assessment-metadata",
        content=b"{}",
        headers={"Content-Type": "text/plain"},
    )
    assert media.json()["error"]["code"] == ERROR_UNSUPPORTED_MEDIA_TYPE
    bad = client.post(
        "/api/v1/assessment-metadata",
        content=b"{",
        headers={"Content-Type": "application/json"},
    )
    assert bad.json()["error"]["code"] == ERROR_MALFORMED_JSON
    schema = client.post(
        "/api/v1/assessment-metadata",
        json=valid_assessment_metadata_body(schema_version="2.0"),
    )
    assert schema.status_code == 422
    assert schema.json()["error"]["code"] == ERROR_UNSUPPORTED_ASSESSMENT_METADATA_SCHEMA


def test_first_accepted_202() -> None:
    client, sink, store, _, tel_sink = configured_metadata_client()
    first = client.post("/api/v1/assessment-metadata", json=valid_assessment_metadata_body())
    assert first.status_code == 202
    body = first.json()
    assert body["status"] == "accepted"
    assert body["retry_status"] == "first_seen"
    assert body["schema_version"] == "1.0"
    assert body["safe_event_reference"].startswith("evt-")
    assert "event_id" not in body
    assert "finding_count" not in body
    assert "repository" not in body
    assert list(body.keys()) == sorted(body.keys())
    assert len(sink.events) == 1
    assert len(store._items) == 1  # noqa: SLF001
    assert tel_sink.events == []
    expected = AssessmentMetadataResponse(
        status=AssessmentMetadataIngestionStatus.ACCEPTED,
        safe_event_reference=body["safe_event_reference"],
        retry_status=body["retry_status"],
        schema_version=body["schema_version"],
    )
    assert first.content == dumps_stable(expected)


def test_default_fail_closed_and_unavailable_sink() -> None:
    client = TestClient(create_community_cloud_app(authentication_policy=disabled_authentication_policy()))
    response = client.post(
        "/api/v1/assessment-metadata", json=valid_assessment_metadata_body()
    )
    assert response.status_code == 503
    assert (
        response.json()["error"]["code"] == ERROR_ASSESSMENT_METADATA_IDENTITY_UNAVAILABLE
    )

    store = InMemoryEventIdentityStore()
    client2 = TestClient(
        create_community_cloud_app(
            assessment_metadata_sink=UnavailableAssessmentMetadataSink(),
            event_identity_lookup=store,
            event_identity_recorder=store,
                authentication_policy=disabled_authentication_policy(),
    )
    )
    response2 = client2.post(
        "/api/v1/assessment-metadata", json=valid_assessment_metadata_body()
    )
    assert response2.status_code == 503
    assert response2.json()["error"]["code"] == ERROR_ASSESSMENT_METADATA_SINK_UNAVAILABLE


def test_six_production_routes_and_health_regression() -> None:
    client, *_ = configured_metadata_client()
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.headers["Cache-Control"] == "no-store"
    paths = {
        (r.method, r.path)
        for r in create_community_cloud_app(authentication_policy=disabled_authentication_policy()).state.community_cloud_route_registry.list_routes()
    }
    assert paths == {
        ("GET", "/health"),
        ("POST", "/ai-usage"),
        ("POST", "/assessment-metadata"),
        ("POST", "/cli-events"),
        ("POST", "/extension-events"),
        ("POST", "/telemetry"),
    }
