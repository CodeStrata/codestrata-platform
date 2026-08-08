"""Browser validation posture checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, frontend_blob
from verification.community_insights_auth.inventory import read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_browser_validation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    auth_client = read_text(monorepo, "insights/src/api/authClient.ts")
    blob = frontend_blob(monorepo)

    add_check(
        checks,
        defects,
        "browser:fetch_credentials",
        'credentials: "include"' in auth_client,
        "include",
        "frontend",
    )
    add_check(
        checks,
        defects,
        "browser:no_document_cookie_session",
        "document.cookie" not in blob,
        "absent",
        "frontend",
    )
    return checks, defects
