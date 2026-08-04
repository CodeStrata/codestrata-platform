"""Production-foundation and deployment-adapter verification."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.deployment import (
    create_production_foundation_app,
    get_handler,
    load_deployment_settings,
)
from codestrata_platform.community_cloud_api.errors import ERROR_AUTHENTICATION_UNAVAILABLE

from verification.community_cloud_api.app_factory import build_production_foundation_client
from verification.community_cloud_api.contract import INGESTION_PATHS
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.models import CheckResult
from verification.community_cloud_api.requests import body_for


def check_deployment_foundation() -> list[CheckResult]:
    client = build_production_foundation_client()
    health = client.get("/api/v1/health")
    ingest = client.post(
        INGESTION_PATHS["telemetry"],
        json=body_for("telemetry", event_id="sv7-prod-1"),
        headers=auth_headers(),
    )
    checks = [
        CheckResult(
            name="foundation:health_ok",
            ok=health.status_code == 200 and health.json().get("status") == "ok",
            detail=f"status={health.status_code}",
            category="deployment_foundation",
        ),
        CheckResult(
            name="foundation:ingestion_fail_closed",
            ok=ingest.status_code == 503
            and ingest.json()["error"]["code"] == ERROR_AUTHENTICATION_UNAVAILABLE,
            detail=f"status={ingest.status_code}",
            category="deployment_foundation",
            scenario="G",
        ),
        CheckResult(
            name="foundation:no_false_accept",
            ok=ingest.json().get("status") != "accepted",
            detail="no false 202",
            category="deployment_foundation",
        ),
    ]

    app = create_production_foundation_app(settings=load_deployment_settings({}))
    registry = app.state.community_cloud_route_registry
    checks.append(
        CheckResult(
            name="foundation:six_routes_retained",
            ok=registry.diagnostics().registered_route_count == 6,
            detail=f"count={registry.diagnostics().registered_route_count}",
            category="deployment_foundation",
        )
    )
    checks.append(
        CheckResult(
            name="foundation:docs_disabled",
            ok=app.docs_url is None and app.openapi_url is None,
            detail="openapi/docs disabled",
            category="deployment_foundation",
        )
    )

    handler = get_handler()
    checks.append(
        CheckResult(
            name="foundation:mangum_handler_importable",
            ok=callable(handler),
            detail="handler present",
            category="deployment_foundation",
        )
    )
    return checks
