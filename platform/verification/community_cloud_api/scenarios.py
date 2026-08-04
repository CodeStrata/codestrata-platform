"""Scenario orchestration for SV.7 negative and positive suites."""

from __future__ import annotations

from verification.community_cloud_api.app_factory import VerificationApp
from verification.community_cloud_api.authentication import (
    check_authentication,
    check_client_matching,
)
from verification.community_cloud_api.contract import INGESTION_KINDS, INGESTION_PATHS
from verification.community_cloud_api.credentials import auth_headers, token_for_kind
from verification.community_cloud_api.models import CheckResult
from verification.community_cloud_api.requests import body_for


def check_happy_path_ingestion(app: VerificationApp) -> list[CheckResult]:
    checks: list[CheckResult] = []
    for kind in INGESTION_KINDS:
        path = INGESTION_PATHS[kind]
        before = app.sink_count(kind)
        response = app.client.post(
            path,
            json=body_for(kind, event_id=f"sv7-happy-{kind}"),
            headers=auth_headers(token_for_kind(kind)),
        )
        checks.append(
            CheckResult(
                name=f"endpoint:accept:{kind}",
                ok=response.status_code == 202
                and response.json().get("status") == "accepted"
                and app.sink_count(kind) == before + 1,
                detail=f"status={response.status_code}",
                category="endpoints",
            )
        )
    return checks


def run_core_scenarios(app: VerificationApp) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.extend(check_happy_path_ingestion(app))
    checks.extend(check_authentication(app))
    checks.extend(check_client_matching(app))
    return checks
