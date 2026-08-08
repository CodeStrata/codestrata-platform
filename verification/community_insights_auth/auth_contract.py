"""Auth contract checks for Slice 15.9 verification."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check
from verification.community_insights_auth.contract import AUTH_CONTRACT_RELATIVE
from verification.community_insights_auth.inventory import load_json
from verification.community_insights_auth.models import CheckResult, Defect


def check_auth_contract(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    contract = load_json(monorepo, AUTH_CONTRACT_RELATIVE)

    add_check(checks, defects, "contract:present", bool(contract), "present", "contract")
    add_check(
        checks,
        defects,
        "contract:id",
        contract.get("contract_id") == "community-insights-auth-contract",
        "configured",
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:password_value_in_source_false",
        contract.get("password_value_in_source") is False,
        "absent",
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:password_value_in_frontend_false",
        contract.get("password_value_in_frontend") is False,
        "absent",
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:password_value_in_terraform_false",
        contract.get("password_value_in_terraform_default") is False,
        "absent",
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:protected_routes",
        "insights.api.overview" in (contract.get("protected_routes") or []),
        "overview",
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:public_auth_routes",
        {"insights.auth.login", "insights.auth.logout", "insights.auth.session"}.issubset(
            set(contract.get("public_auth_routes") or [])
        ),
        "login_logout_session",
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:aggregation_unaware_of_password",
        contract.get("aggregation_unaware_of_password") is True,
        "separate",
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:start_slice_15_11_false",
        contract.get("start_slice_16_3", False) is False,
        "false",
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:production_deployment_enabled_false",
        contract.get("production_deployment_enabled") is False,
        "disabled",
        "contract",
    )
    return checks, defects
