"""Runtime session token checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, ensure_platform_importable
from verification.community_insights_auth.models import CheckResult, Defect


def check_session_runtime(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ensure_platform_importable(monorepo)

    from codestrata_platform.community_cloud_api.insights_auth.secrets import TEST_SESSION_SECRET
    from codestrata_platform.community_cloud_api.insights_auth.session import (
        SessionError,
        create_session_token,
        validate_session_token,
    )

    token = create_session_token(
        signing_secret=TEST_SESSION_SECRET,
        ttl_seconds=60,
        now=lambda: 1000,
    )
    claims = validate_session_token(
        token, signing_secret=TEST_SESSION_SECRET, now=lambda: 1010
    )
    add_check(
        checks,
        defects,
        "runtime:session_create_validate",
        claims.authenticated is True,
        "ok",
        "runtime",
    )

    expired_ok = False
    try:
        validate_session_token(
            token, signing_secret=TEST_SESSION_SECRET, now=lambda: 1061
        )
    except SessionError as exc:
        expired_ok = exc.code == "session_expired"
    add_check(
        checks,
        defects,
        "runtime:session_expired",
        expired_ok,
        "expired",
        "runtime",
    )

    invalid_ok = False
    try:
        validate_session_token(
            token, signing_secret="wrong-signing-key", now=lambda: 1005
        )
    except SessionError as exc:
        invalid_ok = exc.code == "invalid_session"
    add_check(
        checks,
        defects,
        "runtime:session_wrong_sig",
        invalid_ok,
        "rejected",
        "runtime",
    )
    return checks, defects
