"""API-level security and tenant-isolation hardening tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from codestrata_platform.api import create_app
from codestrata_platform.api.security import PLATFORM_API_KEY_ENV, PLATFORM_ENV_VAR


def test_api_key_required_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PLATFORM_ENV_VAR, "development")
    monkeypatch.setenv(PLATFORM_API_KEY_ENV, "test-platform-key")
    app = create_app(use_memory=True)
    with TestClient(app) as client:
        denied = client.get("/api/v1/organizations")
        assert denied.status_code == 401
        allowed = client.get(
            "/api/v1/organizations",
            headers={"Authorization": "Bearer test-platform-key"},
        )
        assert allowed.status_code != 401
        assert client.get("/health").status_code == 200


def test_omitting_tenant_scope_on_executive_api_returns_422(client: TestClient) -> None:
    response = client.get("/api/v1/executive-intelligence/exec:1")
    assert response.status_code == 422


def test_omitting_tenant_scope_on_roadmap_api_returns_422(client: TestClient) -> None:
    response = client.get("/api/v1/executive-intelligence/exec:1/roadmap")
    assert response.status_code == 422
