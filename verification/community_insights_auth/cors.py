"""CORS posture checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, ensure_platform_importable
from verification.community_insights_auth.contract import AUTH_PACKAGE
from verification.community_insights_auth.inventory import load_json, read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_cors(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, "platform/policies/community_insights_auth_policy.json")
    cors_py = read_text(monorepo, f"{AUTH_PACKAGE}/cors.py")

    add_check(
        checks,
        defects,
        "cors:wildcard_disabled",
        policy.get("cors_wildcard_with_credentials") is False,
        "disabled",
        "cors_csrf",
    )
    add_check(
        checks,
        defects,
        "cors:no_wildcard_in_code",
        "Access-Control-Allow-Origin: *" not in cors_py,
        "absent",
        "cors_csrf",
    )
    add_check(
        checks,
        defects,
        "cors:explicit_origin_only",
        "Access-Control-Allow-Origin" in cors_py and "extra_allowed_origins" in cors_py,
        "explicit",
        "cors_csrf",
    )

    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights_auth.cors import cors_headers_for_origin
    from codestrata_platform.community_cloud_api.insights_auth.policy import (
        default_insights_auth_policy,
    )

    headers = cors_headers_for_origin(
        request_origin="https://insights.codestrata.ai",
        policy=default_insights_auth_policy(),
    )
    add_check(
        checks,
        defects,
        "cors:allowed_origin_headers",
        headers is not None and headers.get("Access-Control-Allow-Credentials") == "true",
        "ok",
        "cors_csrf",
    )
    return checks, defects
