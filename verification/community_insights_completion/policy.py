"""Completion policy checks for Slice 15.12."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    TOTAL_SLICES,
)
from verification.community_insights_completion.inventory import load_json
from verification.community_insights_completion.models import CheckResult, Defect


def check_completion_policy(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "completion_policy"))
        if not ok:
            defects.append(Defect("completion_policy", name, "required", detail))

    add("policy:present", bool(policy), "present" if policy else "missing")
    add("policy:id", policy.get("policy_id") == POLICY_ID, str(policy.get("policy_id")))
    add(
        "policy:version",
        policy.get("policy_version") == POLICY_VERSION,
        str(policy.get("policy_version")),
    )
    add("policy:epic", policy.get("epic") == 15, str(policy.get("epic")))
    add(
        "policy:slice_count",
        policy.get("slice_count") == TOTAL_SLICES,
        str(policy.get("slice_count")),
    )
    for flag in (
        "data_lake_audit_complete",
        "partition_strategy_complete",
        "event_coverage_complete",
        "ingestion_hardening_complete",
        "bounded_query_strategy_complete",
        "metric_contract_complete",
        "aggregation_service_complete",
        "insights_application_complete",
        "authentication_complete",
        "dashboard_complete",
        "validation_complete",
        "direct_s3_strategy",
        "epic_complete",
    ):
        add(f"policy:{flag}", policy.get(flag) is True, str(policy.get(flag)))
    for flag in (
        "athena_required",
        "glue_required",
        "analytics_database_required",
        "redis_required",
        "production_ingestion_enabled",
        "live_dashboard_data_available",
        "insights_site_deployed",
        "real_secrets_configured",
        "deployed",
        "start_epic_17",
    ):
        add(f"policy:{flag}_false", policy.get(flag) is False, str(policy.get(flag)))
    add("policy:start_slice_16_5_true", policy.get("start_slice_16_5") is True, str(policy.get("start_slice_16_5")))
    add("policy:start_slice_16_6_true", policy.get("start_slice_16_6") is True, str(policy.get("start_slice_16_6")))
    add("policy:start_slice_16_7_true", policy.get("start_slice_16_7") is True, str(policy.get("start_slice_16_7")))
    add("policy:start_slice_16_8_true", policy.get("start_slice_16_8") is True, str(policy.get("start_slice_16_8")))
    add("policy:start_slice_16_9_true", policy.get("start_slice_16_9") is True, str(policy.get("start_slice_16_9")))
    add("policy:start_slice_16_10_true", policy.get("start_slice_16_10") is True, str(policy.get("start_slice_16_10")))
    add("policy:start_epic_16_true", policy.get("start_epic_16") is True, str(policy.get("start_epic_16")))
    verification = policy.get("verification") or {}
    add(
        "policy:verification_package",
        verification.get("package") == "verification/community_insights_completion",
        str(verification.get("package")),
    )
    return checks, defects
