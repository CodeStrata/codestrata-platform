"""Frontend auth flow checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, frontend_blob
from verification.community_insights_auth.contract import FRONTEND_AUTH_FILES
from verification.community_insights_auth.inventory import exists, read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_frontend_flow(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for rel in FRONTEND_AUTH_FILES:
        add_check(
            checks,
            defects,
            f"frontend:file:{rel.rsplit('/', 1)[-1]}",
            exists(monorepo, rel),
            "present",
            "frontend",
        )

    app = read_text(monorepo, "insights/src/app/App.tsx")
    add_check(
        checks,
        defects,
        "frontend:route_protection",
        "ProtectedApp" in app and "unauthenticated" in app and "LoginPage" in app,
        "protected",
        "frontend",
    )
    add_check(
        checks,
        defects,
        "frontend:auth_provider",
        "AuthProvider" in app and "useAuth" in read_text(monorepo, "insights/src/auth/AuthContext.tsx"),
        "present",
        "frontend",
    )
    return checks, defects
