"""ASGI integration smoke for Insights auth routes."""

from __future__ import annotations

import json

from starlette.testclient import TestClient

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.insights_auth.password import hash_password
from codestrata_platform.community_cloud_api.insights_auth.policy import (
    default_insights_auth_policy,
)
from codestrata_platform.community_cloud_api.insights_auth.secrets import (
    DEFAULT_PASSWORD_SECRET_ID,
    DEFAULT_SESSION_SECRET_ID,
    FakeSecretsPort,
    TEST_PASSWORD_PLAINTEXT,
    TEST_SESSION_SECRET,
)
from codestrata_platform.community_cloud_api.insights_auth.service import InsightsAuthService


def _client() -> TestClient:
    secrets = FakeSecretsPort(
        {
            DEFAULT_PASSWORD_SECRET_ID: hash_password(TEST_PASSWORD_PLAINTEXT),
            DEFAULT_SESSION_SECRET_ID: TEST_SESSION_SECRET,
        }
    )
    auth = InsightsAuthService(
        policy=default_insights_auth_policy(),
        secrets=secrets,
        now=lambda: 1_700_000_000,
        extra_allowed_origins=frozenset({"http://localhost:5173"}),
    )
    app = create_community_cloud_app(insights_auth_service=auth)
    return TestClient(app, base_url="https://testserver")


def test_overview_requires_auth() -> None:
    client = _client()
    res = client.get("/api/v1/insights/api/overview")
    assert res.status_code == 401
    body = res.json()
    assert body["error"]["code"] == "authentication_required"


def test_login_session_overview_logout() -> None:
    client = _client()
    origin = "https://insights.codestrata.ai"
    bad = client.post(
        "/api/v1/insights/auth/login",
        json={"password": "wrong"},
        headers={"Origin": origin},
    )
    assert bad.status_code == 401
    assert "Invalid password" in json.dumps(bad.json())

    ok = client.post(
        "/api/v1/insights/auth/login",
        json={"password": TEST_PASSWORD_PLAINTEXT},
        headers={"Origin": origin},
    )
    assert ok.status_code == 200
    assert "set-cookie" in {k.lower() for k in ok.headers.keys()}

    session = client.get("/api/v1/insights/auth/session")
    assert session.status_code == 200
    assert session.json()["authenticated"] is True

    overview = client.get("/api/v1/insights/api/overview")
    assert overview.status_code == 200
    payload = overview.json()
    assert "metrics" in payload
    dumped = json.dumps(payload)
    assert "installation_id" not in dumped
    assert "model_id" not in dumped
    assert TEST_PASSWORD_PLAINTEXT not in dumped
    assert TEST_SESSION_SECRET not in dumped

    out = client.post(
        "/api/v1/insights/auth/logout",
        headers={"Origin": origin},
    )
    assert out.status_code == 200
    session2 = client.get("/api/v1/insights/auth/session")
    assert session2.json()["authenticated"] is False
