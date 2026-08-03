"""Community Cloud API health endpoint (Slice 7.2)."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

import json
import re

import pytest
from fastapi.testclient import TestClient

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform import __version__ as PLATFORM_VERSION
from codestrata_platform.community_cloud_api import (
    API_PREFIX_V1,
    API_VERSION_V1,
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    RouteRegistry,
    RouteSpec,
    create_community_cloud_app,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_METHOD_NOT_ALLOWED,
    ERROR_NOT_FOUND,
    ERROR_UNSUPPORTED_MEDIA_TYPE,
)
from codestrata_platform.community_cloud_api.health import (
    HEALTH_PATH,
    HEALTH_ROUTE_NAME,
    HEALTH_SERVICE_NAME,
    CommunityHealthResponse,
    register_health_routes,
)
from codestrata_platform.community_cloud_api.serialization import dumps_stable
from codestrata_platform.intelligence_reporting.application.website_export import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_community_cloud_app(authentication_policy=disabled_authentication_policy()))


def test_health_route_registered_through_central_registry() -> None:
    registry = RouteRegistry()
    register_health_routes(registry)
    routes = registry.list_routes()
    assert len(routes) == 1
    route = routes[0]
    assert route.version == API_VERSION_V1
    assert route.method == "GET"
    assert route.path == HEALTH_PATH
    assert route.name == HEALTH_ROUTE_NAME
    assert route.absolute_path == f"{API_PREFIX_V1}/health"
    assert registry.get_handler(route) is not None


def test_health_duplicate_registration_rejected() -> None:
    registry = RouteRegistry()
    register_health_routes(registry)
    with pytest.raises(ValueError, match="duplicate route"):
        register_health_routes(registry)


def test_foundation_registry_includes_health_under_v1() -> None:
    registry = RouteRegistry.foundation_v1()
    assert registry.get(version="v1", method="GET", path="/health") is not None
    assert registry.get(version="v1", method="POST", path="/telemetry") is not None
    assert registry.diagnostics().registered_route_count == 6


def test_get_health_returns_200_json(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Community-Cloud-API-Version"] == "v1"
    body = response.json()
    assert body == {
        "api_version": "v1",
        "application_version": PLATFORM_VERSION,
        "schema_version": "1.0",
        "service": HEALTH_SERVICE_NAME,
        "status": "ok",
    }
    assert list(body.keys()) == sorted(body.keys())


def test_health_body_deterministic(client: TestClient) -> None:
    first = client.get("/api/v1/health").content
    second = client.get("/api/v1/health").content
    assert first == second
    assert dumps_stable(CommunityHealthResponse.build()) == first


def test_health_excludes_request_id_from_body(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-Id": "probe-1"})
    assert response.status_code == 200
    assert "request_id" not in response.json()
    assert response.headers["X-Request-Id"] == "probe-1"


def test_health_rejects_non_get_methods(client: TestClient) -> None:
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        response = client.request(method, "/api/v1/health")
        assert response.status_code == 405, method
        assert response.json()["error"]["code"] == ERROR_METHOD_NOT_ALLOWED


def test_unsupported_media_type_unchanged(client: TestClient) -> None:
    response = client.post(
        "/api/v1/health",
        content=b"x",
        headers={"Content-Type": "text/plain"},
    )
    # Method rejection may win before media-type checks depending on path;
    # either 405 (method) or 415 (media) is foundation-safe. Prefer method.
    assert response.status_code in {405, 415}
    assert response.json()["error"]["code"] in {
        ERROR_METHOD_NOT_ALLOWED,
        ERROR_UNSUPPORTED_MEDIA_TYPE,
    }


def test_unknown_routes_still_404(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == ERROR_NOT_FOUND


def test_get_telemetry_is_method_not_allowed(client: TestClient) -> None:
    response = client.get("/api/v1/telemetry")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == ERROR_METHOD_NOT_ALLOWED


def test_health_safety_no_infrastructure_leakage(client: TestClient) -> None:
    text = client.get("/api/v1/health").text
    body = json.loads(text)
    forbidden_keys = {
        "timestamp",
        "hostname",
        "host",
        "pid",
        "process_id",
        "environment",
        "env",
        "region",
        "account",
        "cloud",
        "deployment",
        "routes",
        "registered_route_count",
        "dependencies",
        "database",
        "stack",
        "traceback",
    }
    assert forbidden_keys.isdisjoint(body.keys())
    assert not re.search(r"/Users/|/home/|\\\\", text)
    assert "Traceback" not in text
    assert "AWS" not in text
    assert "GITHUB_TOKEN" not in text
    assert "SECRET" not in text.upper()


def test_health_model_uses_canonical_constants() -> None:
    model = CommunityHealthResponse.build()
    assert model.status == "ok"
    assert model.service == "codestrata-community-cloud-api"
    assert model.api_version == API_VERSION_V1
    assert model.schema_version == COMMUNITY_CLOUD_API_SCHEMA_VERSION
    assert model.application_version == PLATFORM_VERSION


def test_root_health_still_404_on_community_cloud_app(client: TestClient) -> None:
    # Commercial Platform /health is a different app surface.
    assert client.get("/health").status_code == 404


def test_production_routes_are_health_telemetry_and_assessment_metadata() -> None:
    registry = RouteRegistry.foundation_v1()
    paths = {(r.method, r.path) for r in registry.list_routes()}
    assert paths == {("GET", "/health"), ("POST", "/ai-usage"), ("POST", "/assessment-metadata"), ("POST", "/cli-events"), ("POST", "/extension-events"), ("POST", "/telemetry")}


def test_schema_constants_unchanged() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"


def test_registered_without_handler_still_404() -> None:
    registry = RouteRegistry()
    registry.register(
        RouteSpec(version="v1", method="GET", path="/health", name="health.get")
    )
    # No handler bound — remains unimplemented.
    client = TestClient(create_community_cloud_app(registry=registry,
        authentication_policy=disabled_authentication_policy(),
    ))
    assert client.get("/api/v1/health").status_code == 404
