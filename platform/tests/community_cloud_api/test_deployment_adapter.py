"""Community Cloud Lambda deployment adapter tests (Slice 7.14)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from codestrata_platform.community_cloud_api.authentication import (
    UnavailableCommunityCredentialVerifier,
)
from codestrata_platform.community_cloud_api.deployment import (
    create_production_foundation_app,
    load_deployment_settings,
)
from codestrata_platform.community_cloud_api.deployment.settings import (
    DEPLOYMENT_MODE_PRODUCTION_FOUNDATION,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_AUTHENTICATION_UNAVAILABLE,
)

from .telemetry_helpers import valid_telemetry_body


def test_load_settings_defaults_fail_closed() -> None:
    settings = load_deployment_settings({})
    assert settings.deployment_mode == DEPLOYMENT_MODE_PRODUCTION_FOUNDATION
    assert settings.authentication_enabled is True
    assert settings.rate_limit_enabled is True
    assert settings.ingestion_enabled is False


def test_load_settings_rejects_ingestion_enabled() -> None:
    with pytest.raises(ValueError, match="INGESTION_ENABLED"):
        load_deployment_settings({"CODESTRATA_INGESTION_ENABLED": "true"})


def test_load_settings_rejects_auth_disabled() -> None:
    with pytest.raises(ValueError, match="AUTHENTICATION_ENABLED"):
        load_deployment_settings({"CODESTRATA_AUTHENTICATION_ENABLED": "false"})


def test_production_app_health_and_route_count() -> None:
    app = create_production_foundation_app(settings=load_deployment_settings({}))
    registry = app.state.community_cloud_route_registry
    assert registry.diagnostics().registered_route_count == 6
    assert app.docs_url is None
    assert app.openapi_url is None

    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["schema_version"] == "1.0"


def test_production_wiring_uses_unavailable_verifier() -> None:
    app = create_production_foundation_app(settings=load_deployment_settings({}))
    runtime = app.state.community_cloud_authentication_runtime
    assert isinstance(runtime.verifier, UnavailableCommunityCredentialVerifier)
    diagnostic = app.state.community_cloud_deployment_diagnostic
    assert diagnostic["credential_verifier"] == "unavailable"
    assert diagnostic["durable_ingestion"] is False


def test_production_ingestion_fail_closed() -> None:
    client = TestClient(
        create_production_foundation_app(settings=load_deployment_settings({}))
    )
    response = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == ERROR_AUTHENTICATION_UNAVAILABLE


def test_production_ingestion_with_bearer_still_fail_closed() -> None:
    client = TestClient(
        create_production_foundation_app(settings=load_deployment_settings({}))
    )
    response = client.post(
        "/api/v1/telemetry",
        headers={"Authorization": "Bearer cscc_v1_notarealtokenvalue00"},
        json=valid_telemetry_body(),
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == ERROR_AUTHENTICATION_UNAVAILABLE


def test_lambda_handler_import_and_app() -> None:
    from codestrata_platform.community_cloud_api.deployment import lambda_handler

    app = lambda_handler.get_app()
    assert (
        app.state.community_cloud_route_registry.diagnostics().registered_route_count
        == 6
    )
    pytest.importorskip("mangum")
    handler = lambda_handler.get_handler()
    assert callable(handler)


def test_no_test_sinks_in_production_wiring_source() -> None:
    source = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "deployment"
        / "wiring.py"
    )
    text = source.read_text(encoding="utf-8")
    assert "UnavailableCommunityCredentialVerifier" in text
    assert "build_test_verifier" not in text
    assert "InMemoryTelemetryEventSink" not in text
    assert "Recording" not in text
    assert "disabled_authentication_policy" not in text
