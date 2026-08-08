"""Auth runtime checks with TestClient."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_insights_validation._common import add_check, ensure_platform_importable
from verification.community_insights_validation.fixtures import bounded_reader
from verification.community_insights_validation.models import CheckResult, Defect


def _test_client(monorepo: Path):
    ensure_platform_importable(monorepo)
    from starlette.testclient import TestClient

    from codestrata_platform.community_cloud_api.app import create_community_cloud_app
    from codestrata_platform.community_cloud_api.insights.service import InsightsAggregationService
    from codestrata_platform.community_cloud_api.insights.validation_dataset import (
        LocalValidationCatalogReader,
    )
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

    reader, _fx = bounded_reader(monorepo)
    aggregation = InsightsAggregationService(
        reader=reader,
        validation_catalog=LocalValidationCatalogReader(monorepo),
    )
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
        extra_allowed_origins=frozenset({"https://insights.codestrata.ai"}),
    )
    app = create_community_cloud_app(
        insights_auth_service=auth,
        insights_aggregation_service=aggregation,
    )
    return TestClient(app, base_url="https://testserver"), TEST_PASSWORD_PLAINTEXT, TEST_SESSION_SECRET


def check_auth(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    client, password, session_secret = _test_client(monorepo)
    origin = "https://insights.codestrata.ai"

    unauth = client.get("/api/v1/insights/api/overview")
    add_check(
        checks,
        defects,
        "auth:overview_requires_auth",
        unauth.status_code == 401
        and unauth.json().get("error", {}).get("code") == "authentication_required",
        str(unauth.status_code),
        "auth",
    )

    login = client.post(
        "/api/v1/insights/auth/login",
        json={"password": password},
        headers={"Origin": origin},
    )
    add_check(
        checks,
        defects,
        "auth:login_success",
        login.status_code == 200,
        str(login.status_code),
        "auth",
    )

    overview = client.get("/api/v1/insights/api/overview")
    payload_text = json.dumps(overview.json())
    add_check(
        checks,
        defects,
        "auth:overview_authenticated",
        overview.status_code == 200 and "metrics" in overview.json(),
        str(overview.status_code),
        "auth",
    )
    for forbidden in ("installation_id", "model_id", "s3_key"):
        add_check(
            checks,
            defects,
            f"auth:overview_no_{forbidden}",
            forbidden not in payload_text,
            "absent",
            "auth",
        )
    add_check(
        checks,
        defects,
        "auth:overview_no_password",
        password not in payload_text,
        "absent",
        "auth",
    )
    add_check(
        checks,
        defects,
        "auth:overview_no_session_secret",
        session_secret not in payload_text,
        "absent",
        "auth",
    )

    logout = client.post(
        "/api/v1/insights/auth/logout",
        headers={"Origin": origin},
    )
    add_check(
        checks,
        defects,
        "auth:logout_success",
        logout.status_code == 200,
        str(logout.status_code),
        "auth",
    )
    return checks, defects
