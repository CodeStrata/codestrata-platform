"""Policy and contract checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    VALIDATION_CONTRACT_RELATIVE,
)
from verification.community_insights_validation.inventory import load_json
from verification.community_insights_validation.models import CheckResult, Defect


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)

    add_check(checks, defects, "policy:present", bool(policy), "present", "policy")
    add_check(
        checks,
        defects,
        "policy:id",
        policy.get("policy_id") == POLICY_ID,
        str(policy.get("policy_id")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:version",
        policy.get("policy_version") == POLICY_VERSION,
        str(policy.get("policy_version")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:slice",
        policy.get("slice") == "15.11",
        str(policy.get("slice")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:offline_only",
        policy.get("offline_only") is True and policy.get("aws_calls_forbidden") is True,
        "offline",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:cohort_minimum",
        policy.get("cohort_minimum") == 3,
        str(policy.get("cohort_minimum")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:overview_single_request",
        policy.get("overview_single_request_required") is True,
        str(policy.get("overview_single_request_required")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:polling_forbidden",
        policy.get("polling_forbidden") is True,
        str(policy.get("polling_forbidden")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:no_new_dashboard_capability",
        policy.get("no_new_dashboard_capability_in_15_11") is True,
        str(policy.get("no_new_dashboard_capability_in_15_11")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:no_metric_redefinition",
        policy.get("no_metric_redefinition_in_15_11") is True,
        str(policy.get("no_metric_redefinition_in_15_11")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:start_slice_16_3_false",
        policy.get("start_slice_16_3", False) is False,
        str(policy.get("start_slice_16_3", False)),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:production_ingestion_disabled",
        policy.get("production_ingestion_enabled") is False,
        str(policy.get("production_ingestion_enabled")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:live_dashboard_data_unavailable",
        policy.get("live_dashboard_data_available") is False,
        str(policy.get("live_dashboard_data_available")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:athena_forbidden",
        policy.get("athena_glue_rds_redis_forbidden_for_insights") is True,
        str(policy.get("athena_glue_rds_redis_forbidden_for_insights")),
        "policy",
    )
    return checks, defects


def check_contract(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    contract = load_json(monorepo, VALIDATION_CONTRACT_RELATIVE)

    add_check(checks, defects, "contract:present", bool(contract), "present", "contract")
    add_check(
        checks,
        defects,
        "contract:id",
        contract.get("contract_id") == "community-insights-validation-contract",
        str(contract.get("contract_id")),
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:offline_validation",
        contract.get("offline_validation") is True,
        str(contract.get("offline_validation")),
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:synthetic_fixtures",
        contract.get("synthetic_fixtures_required") is True,
        str(contract.get("synthetic_fixtures_required")),
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:start_slice_16_3_false",
        contract.get("start_slice_16_3", False) is False,
        str(contract.get("start_slice_16_3", False)),
        "contract",
    )
    add_check(
        checks,
        defects,
        "contract:production_ingestion_disabled",
        contract.get("production_ingestion_enabled") is False,
        str(contract.get("production_ingestion_enabled")),
        "contract",
    )
    must_not = contract.get("report_must_not_contain") or []
    for field, label in (
        ("installation_id_values", "installation_id_values"),
        ("passwords", "passwords"),
        ("session_tokens", "session_tokens"),
        ("absolute_paths", "absolute_paths"),
        ("timestamps", "time_values"),
        ("aws_secret_values", "aws_secret_values"),
    ):
        add_check(
            checks,
            defects,
            f"contract:report_no_{label}",
            field in must_not,
            "listed",
            "contract",
        )
    return checks, defects
