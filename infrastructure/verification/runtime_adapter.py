"""In-process production-foundation runtime adapter verification."""

from __future__ import annotations

from fastapi.testclient import TestClient

from codestrata_platform.community_cloud_api.deployment import (
    create_production_foundation_app,
    get_handler,
    load_deployment_settings,
)
from codestrata_platform.community_cloud_api.errors import ERROR_AUTHENTICATION_UNAVAILABLE

from infrastructure.verification.contract import INGESTION_PATHS
from infrastructure.verification.models import CheckResult

_FAKE_TOKEN = "cscc_v1_TEST_ONLY_SHOULD_NOT_ACCEPT"


def check_runtime_adapter() -> list[CheckResult]:
    settings = load_deployment_settings({})
    app = create_production_foundation_app(settings=settings)
    client = TestClient(app)
    health = client.get("/api/v1/health")
    registry = app.state.community_cloud_route_registry
    checks = [
        CheckResult(
            name="runtime:health_200",
            ok=health.status_code == 200 and health.json().get("status") == "ok",
            detail=f"status={health.status_code}",
            category="runtime",
        ),
        CheckResult(
            name="runtime:six_routes",
            ok=registry.diagnostics().registered_route_count == 6,
            detail=f"count={registry.diagnostics().registered_route_count}",
            category="runtime",
        ),
        CheckResult(
            name="runtime:docs_disabled",
            ok=app.docs_url is None and app.openapi_url is None,
            detail="no openapi/docs",
            category="runtime",
        ),
        CheckResult(
            name="runtime:mangum_handler",
            ok=callable(get_handler()),
            detail="handler importable",
            category="runtime",
        ),
        CheckResult(
            name="runtime:settings_fail_closed",
            ok=(
                settings.deployment_mode == "production_foundation"
                and settings.authentication_enabled
                and settings.rate_limit_enabled
                and not settings.ingestion_enabled
            ),
            detail="foundation settings",
            category="runtime",
        ),
    ]

    for path in INGESTION_PATHS:
        response = client.post(
            path,
            json={"schema_version": "1.0"},
            headers={"Authorization": f"Bearer {_FAKE_TOKEN}"},
        )
        body = response.json()
        checks.append(
            CheckResult(
                name=f"runtime:fail_closed:{path.rsplit('/', 1)[-1]}",
                ok=(
                    response.status_code == 503
                    and body.get("error", {}).get("code")
                    == ERROR_AUTHENTICATION_UNAVAILABLE
                    and body.get("status") not in {"accepted", "already_accepted"}
                    and response.status_code != 202
                ),
                detail=f"status={response.status_code}",
                category="runtime",
                scenario="Y",
            )
        )
    return checks
