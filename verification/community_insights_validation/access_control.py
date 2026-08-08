"""Access control checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.contract import VALIDATION_CONTRACT_RELATIVE
from verification.community_insights_validation.inventory import load_json, read_text
from verification.community_insights_validation.models import CheckResult, Defect


def check_access_control(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    auth_contract = load_json(
        monorepo, "platform/policies/community_insights_auth_contract.json"
    )
    handlers = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/insights_auth/handlers.py",
    )
    app = read_text(monorepo, "insights/src/app/App.tsx")

    add_check(
        checks,
        defects,
        "access:overview_protected_route",
        "insights.api.overview" in (auth_contract.get("protected_routes") or []),
        "listed",
        "access_control",
    )
    add_check(
        checks,
        defects,
        "access:require_authenticated_handler",
        "require_authenticated" in handlers,
        "present",
        "access_control",
    )
    add_check(
        checks,
        defects,
        "access:protected_app_shell",
        "ProtectedApp" in app,
        "present",
        "access_control",
    )
    add_check(
        checks,
        defects,
        "access:validation_contract_auth_required",
        "authentication_required" in (load_json(monorepo, VALIDATION_CONTRACT_RELATIVE).get("pass_requires") or []),
        "listed",
        "access_control",
    )
    return checks, defects
