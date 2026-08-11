"""Community Cloud API foundation behavior (Slice 7.1)."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

import json

import pytest
from fastapi.testclient import TestClient

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.community_cloud_api import (
    API_PREFIX_V1,
    API_VERSION_V1,
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    SUPPORTED_API_VERSIONS,
    RouteRegistry,
    RouteSpec,
    create_community_cloud_app,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_METHOD_NOT_ALLOWED,
    ERROR_NOT_FOUND,
    ERROR_VERSION_NOT_SUPPORTED,
    ApiErrorResponse,
)
from codestrata_platform.community_cloud_api.serialization import dumps_stable
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_community_cloud_app(authentication_policy=disabled_authentication_policy()))


def test_api_version_constants() -> None:
    assert API_VERSION_V1 == "v1"
    assert SUPPORTED_API_VERSIONS == ("v1",)
    assert API_PREFIX_V1 == "/api/v1"
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"


def test_registry_foundation_v1_is_deterministic_with_health_telemetry_and_assessment_metadata() -> None:
    left = RouteRegistry.foundation_v1()
    right = RouteRegistry.foundation_v1()
    assert left.list_routes() == right.list_routes()
    assert [(r.method, r.path, r.name) for r in left.list_routes()] == [
        ("GET", "/health", "health.get"),
        ("POST", "/ai-usage", "ai_usage.ingest"),
        ("POST", "/assessment-metadata", "assessment_metadata.ingest"),
        ("POST", "/cli-events", "cli_events.ingest"),
        ("POST", "/extension-events", "extension_events.ingest"),
        ("POST", "/telemetry", "telemetry.ingest"),
    ]
    assert left.list_versions() == ("v1",)
    assert left.prefix_for_version("v1") == "/api/v1"
    assert left.diagnostics().registered_route_count == 6


def test_registry_rejects_duplicates_and_unknown_versions() -> None:
    registry = RouteRegistry()
    registry.register(
        RouteSpec(version="v1", method="GET", path="/future", name="future.get")
    )
    with pytest.raises(ValueError, match="duplicate route"):
        registry.register(
            RouteSpec(version="v1", method="GET", path="/future", name="future.get.other")
        )
    with pytest.raises(ValueError, match="unsupported API version"):
        RouteSpec(version="v9", method="GET", path="/x", name="x")


def test_unknown_route_returns_canonical_404(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == ERROR_NOT_FOUND
    assert payload["error"]["message"] == "Endpoint not found."
    assert payload["meta"]["api_surface"] == "community_cloud"
    assert payload["meta"]["api_version"] == "v1"
    assert payload["meta"]["http_status"] == 404
    assert "Traceback" not in response.text
    assert "/Users/" not in response.text


def test_root_and_non_api_paths_are_404(client: TestClient) -> None:
    assert client.get("/").status_code == 404
    assert client.get("/health").status_code == 404
    assert client.get("/ready").status_code == 404


def test_unsupported_api_version(client: TestClient) -> None:
    response = client.get("/api/v9/things")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == ERROR_VERSION_NOT_SUPPORTED


def test_unsupported_method(client: TestClient) -> None:
    response = client.request("TRACE", "/api/v1/x")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == ERROR_METHOD_NOT_ALLOWED


def test_unknown_post_route_is_404_before_body_validation(client: TestClient) -> None:
    # Route resolution precedes content-type / JSON parsing (Slice 7.3).
    response = client.post(
        "/api/v1/x",
        content=b"not-json",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == ERROR_NOT_FOUND


def test_unknown_post_route_malformed_json_is_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/x",
        content=b"{",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == ERROR_NOT_FOUND


def test_error_serialization_deterministic() -> None:
    left = ApiErrorResponse.build(
        ERROR_NOT_FOUND,
        http_status=404,
        api_version="v1",
        request_id="req-1",
    )
    right = ApiErrorResponse.build(
        ERROR_NOT_FOUND,
        http_status=404,
        api_version="v1",
        request_id="req-1",
    )
    assert dumps_stable(left) == dumps_stable(right)
    text = dumps_stable(left).decode("utf-8")
    assert list(json.loads(text).keys()) == ["error", "meta"]
    assert list(json.loads(text)["error"].keys()) == sorted(
        json.loads(text)["error"].keys()
    )


def test_request_id_echoed_when_supplied(client: TestClient) -> None:
    response = client.get("/api/v1/missing", headers={"X-Request-Id": "fixed-id-1"})
    assert response.status_code == 404
    assert response.headers["X-Request-Id"] == "fixed-id-1"
    assert response.headers["X-Community-Cloud-API-Version"] == "v1"
    assert response.json()["error"]["request_id"] == "fixed-id-1"


def test_only_health_telemetry_and_assessment_metadata_routes_registered_and_openapi_disabled() -> None:
    app = create_community_cloud_app(authentication_policy=disabled_authentication_policy())
    registry: RouteRegistry = app.state.community_cloud_route_registry
    routes = {(r.method, r.path) for r in registry.list_routes()}
    assert {
        ("GET", "/health"),
        ("POST", "/ai-usage"),
        ("POST", "/assessment-metadata"),
        ("POST", "/cli-events"),
        ("POST", "/extension-events"),
        ("POST", "/telemetry"),
    }.issubset(routes)
    assert len(routes) == 19
    assert app.docs_url is None
    assert app.openapi_url is None


def test_registered_but_unimplemented_route_still_404() -> None:
    registry = RouteRegistry.foundation_v1()
    registry.register(
        RouteSpec(version="v1", method="GET", path="/reserved", name="reserved.get")
    )
    client = TestClient(create_community_cloud_app(registry=registry,
        authentication_policy=disabled_authentication_policy(),
    ))
    response = client.get("/api/v1/reserved")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == ERROR_NOT_FOUND
    assert response.json()["error"]["details"]["reason"] == "endpoint_not_implemented"


def test_schema_constants_unchanged_by_this_slice() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"


def test_error_does_not_leak_exception_text() -> None:
    envelope = ApiErrorResponse.build(
        "totally_unknown_code",
        http_status=500,
        message="secret /Users/dev/x traceback",
    )
    body = envelope.to_stable_dict()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["message"] == "An unexpected error occurred."
    assert "/Users/" not in json.dumps(body)
    assert "Traceback" not in json.dumps(body)
    assert "secret" not in json.dumps(body)
