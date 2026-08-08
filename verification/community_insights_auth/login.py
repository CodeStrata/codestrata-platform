"""Runtime login, logout, and session service checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, ensure_platform_importable
from verification.community_insights_auth.models import CheckResult, Defect


def _auth_service(monorepo: Path, *, now: int = 1_700_000_000):
    ensure_platform_importable(monorepo)
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

    secrets = FakeSecretsPort(
        {
            DEFAULT_PASSWORD_SECRET_ID: hash_password(TEST_PASSWORD_PLAINTEXT),
            DEFAULT_SESSION_SECRET_ID: TEST_SESSION_SECRET,
        }
    )
    return InsightsAuthService(
        policy=default_insights_auth_policy(),
        secrets=secrets,
        now=lambda: now,
    )


def check_login_logout_session(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights_auth.secrets import (
        TEST_PASSWORD_PLAINTEXT,
    )

    auth = _auth_service(monorepo)
    cookie, err = auth.login(TEST_PASSWORD_PLAINTEXT)
    add_check(
        checks,
        defects,
        "runtime:login_success",
        err is None and cookie is not None,
        "ok",
        "runtime",
    )

    token = ""
    if cookie:
        token = cookie.split(";", 1)[0].split("=", 1)[1]
    header = f"{auth.policy.cookie_name}={token}"
    claims, cerr = auth.session_from_cookie_header(header)
    add_check(
        checks,
        defects,
        "runtime:session_status",
        cerr is None and claims is not None,
        "authenticated",
        "runtime",
    )

    cleared = auth.logout_cookie()
    add_check(
        checks,
        defects,
        "runtime:logout_clears_cookie",
        "Max-Age=0" in cleared,
        "cleared",
        "runtime",
    )
    return checks, defects


def check_overview_requires_auth(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    auth = _auth_service(monorepo)
    principal, err = auth.require_authenticated(None)
    add_check(
        checks,
        defects,
        "runtime:overview_requires_auth",
        principal is None and err == "authentication_required",
        "required",
        "runtime",
    )
    return checks, defects
