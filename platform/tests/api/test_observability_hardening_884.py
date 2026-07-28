"""Observability and diagnostics hardening regressions (Phase 8.8.4)."""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from codestrata_platform.api import create_app
from codestrata_platform.api.security import PLATFORM_API_KEY_ENV, PLATFORM_ENV_VAR
from codestrata_platform.application.common.diagnostics import (
    DATABASE,
    PROVIDER_TIMEOUT,
    classify_exception,
    safe_failure_summary,
)
from codestrata_platform.application.common.errors import ValidationError
from codestrata_platform.infrastructure.persistence.database import (
    DatabaseConfigurationError,
    get_database_url,
)


def test_request_and_correlation_ids_are_echoed(client: TestClient) -> None:
    response = client.get(
        "/health",
        headers={
            "X-Request-Id": "req-observability-001",
            "X-Correlation-Id": "corr-observability-001",
        },
    )
    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "req-observability-001"
    assert response.headers["X-Correlation-Id"] == "corr-observability-001"


def test_request_id_is_minted_when_absent(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-Id")
    assert response.headers.get("X-Correlation-Id") == response.headers["X-Request-Id"]


def test_ready_memory_mode_is_ready(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["persistence"] == "memory"
    assert "password" not in str(body).lower()
    assert "postgresql+" not in str(body).lower()


def test_api_error_messages_are_secret_safe(client: TestClient) -> None:
    app = client.app

    @app.get("/__test__/leak")
    def _leak() -> None:
        raise ValidationError(
            "db failed postgresql+psycopg://codestrata:super-secret@db/codestrata",
            reason_code="validation_error",
        )

    response = client.get("/__test__/leak")
    assert response.status_code == 422
    message = response.json()["error"]["message"]
    assert "super-secret" not in message
    assert "***" in message or "redacted" in message.lower() or "codestrata:***" in message


def test_unhandled_exception_is_opaque_but_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = create_app(use_memory=True)

    @app.get("/__test__/boom")
    def _boom() -> None:
        raise RuntimeError(
            "boom bearer=sk-secret-token-value "
            "postgresql+psycopg://codestrata:dbpass@db/codestrata"
        )

    with (
        TestClient(app, raise_server_exceptions=False) as test_client,
        caplog.at_level(logging.ERROR),
    ):
        response = test_client.get("/__test__/boom")
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_server_error"
    assert "sk-secret-token-value" not in str(body)
    assert "dbpass" not in str(body)
    assert "An unexpected error occurred" in body["error"]["message"]
    assert any("Unhandled API exception" in record.message for record in caplog.records)
    joined = "\n".join(record.getMessage() for record in caplog.records)
    assert "sk-secret-token-value" not in joined
    assert "dbpass" not in joined


def test_request_validation_details_omit_input(client: TestClient) -> None:
    response = client.post("/api/v1/organizations", json={"name": 123})
    assert response.status_code == 422
    details = response.json()["error"]["details"]
    assert "errors" in details
    for item in details["errors"]:
        assert "input" not in item


def test_production_docs_require_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PLATFORM_ENV_VAR, "production")
    monkeypatch.setenv(PLATFORM_API_KEY_ENV, "prod-key")
    app = create_app(use_memory=True)
    with TestClient(app) as test_client:
        assert test_client.get("/health").status_code == 200
        assert test_client.get("/ready").status_code == 200
        denied = test_client.get("/openapi.json")
        assert denied.status_code == 401
        allowed = test_client.get(
            "/openapi.json",
            headers={"Authorization": "Bearer prod-key"},
        )
        assert allowed.status_code == 200


def test_safe_failure_summary_redacts_database_url() -> None:
    message = (
        "OperationalError: connection failed "
        "postgresql+psycopg://codestrata:hunter2@127.0.0.1:5432/codestrata"
    )
    summary = safe_failure_summary(message, limit=500)
    assert "hunter2" not in summary
    assert len(summary) <= 500


def test_classify_exception_maps_provider_and_database() -> None:
    class TimeoutBoom(Exception):
        pass

    assert classify_exception(TimeoutBoom("provider timeout")) == PROVIDER_TIMEOUT

    class OperationalError(Exception):
        pass

    assert classify_exception(OperationalError("database connection refused")) == DATABASE


def test_database_configuration_errors_do_not_embed_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CODESTRATA_DATABASE_URL", raising=False)
    monkeypatch.delenv("CODESTRATA_PLATFORM_DATABASE_URL", raising=False)
    monkeypatch.delenv("CODESTRATA_PGVECTOR_URL", raising=False)
    with pytest.raises(DatabaseConfigurationError) as exc_info:
        get_database_url()
    text = str(exc_info.value)
    assert "codestrata:codestrata@" not in text
    assert "user:password@" not in text
    assert "***" in text


def test_feature_flag_disabled_returns_bounded_reason(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    monkeypatch.delenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", raising=False)
    response = client.post(
        "/api/v1/portfolios/portfolio:missing/executive-intelligence",
        json={
            "organization_id": "org:1",
            "workspace_id": "ws:1",
        },
    )
    # Disabled or not-found — either way message must stay bounded and secret-free.
    assert response.status_code in {404, 422}
    message = response.json()["error"]["message"]
    assert "traceback" not in message.lower()
    assert "postgresql+" not in message.lower()
