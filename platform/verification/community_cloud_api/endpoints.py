"""Route inventory and health verification."""

from __future__ import annotations

from verification.community_cloud_api.app_factory import VerificationApp, build_verification_app
from verification.community_cloud_api.adapters import tight_rate_limit_policy
from verification.community_cloud_api.contract import EXPECTED_ROUTE_IDENTITIES
from verification.community_cloud_api.models import CheckResult


def check_route_inventory(app: VerificationApp) -> list[CheckResult]:
    registry = app.client.app.state.community_cloud_route_registry
    routes = registry.list_routes()
    names = tuple(sorted(r.name for r in routes))
    paths = {(r.method, r.path) for r in routes}
    checks = [
        CheckResult(
            name="routes:count_current",
            ok=len(routes) == 19,
            detail=f"count={len(routes)}",
            category="routes",
        ),
        CheckResult(
            name="routes:expected_identities",
            ok=set(EXPECTED_ROUTE_IDENTITIES).issubset(set(names)),
            detail=f"names={list(names)}",
            category="routes",
        ),
        CheckResult(
            name="routes:expected_paths",
            ok={
                ("GET", "/health"),
                ("POST", "/telemetry"),
                ("POST", "/assessment-metadata"),
                ("POST", "/cli-events"),
                ("POST", "/extension-events"),
                ("POST", "/ai-usage"),
            }.issubset(paths),
            detail=f"paths={sorted(paths)}",
            category="routes",
        ),
        CheckResult(
            name="routes:no_docs_openapi",
            ok=app.client.app.docs_url is None and app.client.app.openapi_url is None,
            detail="docs/openapi disabled",
            category="routes",
        ),
    ]
    unknown = app.client.get("/api/v1/does-not-exist")
    checks.append(
        CheckResult(
            name="routes:unknown_404",
            ok=unknown.status_code == 404,
            detail=f"status={unknown.status_code}",
            category="routes",
            scenario="A",
        )
    )
    wrong = app.client.post("/api/v1/health", json={})
    checks.append(
        CheckResult(
            name="routes:health_post_405",
            ok=wrong.status_code == 405,
            detail=f"status={wrong.status_code}",
            category="routes",
            scenario="B",
        )
    )
    return checks


def check_health(app: VerificationApp) -> list[CheckResult]:
    first = app.client.get("/api/v1/health")
    second = app.client.get("/api/v1/health", headers={"X-Request-Id": "sv7-health-1"})
    body = first.json()
    checks = [
        CheckResult(
            name="health:status_ok",
            ok=first.status_code == 200 and body.get("status") == "ok",
            detail=f"status={first.status_code}",
            category="health",
        ),
        CheckResult(
            name="health:deterministic_body",
            ok=first.content == second.content,
            detail="bodies equal",
            category="health",
        ),
        CheckResult(
            name="health:no_request_id_in_body",
            ok="request_id" not in body,
            detail="body excludes request_id",
            category="health",
        ),
        CheckResult(
            name="health:cache_control",
            ok=first.headers.get("Cache-Control") == "no-store",
            detail=str(first.headers.get("Cache-Control")),
            category="health",
        ),
        CheckResult(
            name="health:independent_of_sinks",
            ok=app.total_sink_events() == 0,
            detail=f"sinks={app.total_sink_events()}",
            category="health",
        ),
    ]
    # Tight health rate limit
    limited = build_verification_app(rate_limit_policy=tight_rate_limit_policy(health_limit=1))
    assert limited.client.get("/api/v1/health").status_code == 200
    blocked = limited.client.get("/api/v1/health")
    checks.append(
        CheckResult(
            name="health:rate_limit_429",
            ok=blocked.status_code == 429,
            detail=f"status={blocked.status_code}",
            category="health",
            scenario="I",
        )
    )
    return checks
