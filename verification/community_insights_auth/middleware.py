"""Middleware and authorization checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check
from verification.community_insights_auth.contract import AUTH_PACKAGE
from verification.community_insights_auth.inventory import read_text
from verification.community_insights_auth.models import CheckResult, Defect
def check_middleware(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    handlers = read_text(monorepo, f"{AUTH_PACKAGE}/handlers.py")
    add_check(
        checks,
        defects,
        "middleware:handlers_present",
        "handle_login" in handlers and "handle_overview" in handlers,
        "present",
        "platform",
    )
    add_check(
        checks,
        defects,
        "middleware:cache_control_no_store",
        handlers.count("Cache-Control") >= 2,
        "no_store",
        "platform",
    )
    return checks, defects


def check_authorization(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    handlers = read_text(monorepo, f"{AUTH_PACKAGE}/handlers.py")
    add_check(
        checks,
        defects,
        "authorization:overview_checks_auth",
        "require_authenticated" in handlers,
        "required",
        "platform",
    )
    return checks, defects
