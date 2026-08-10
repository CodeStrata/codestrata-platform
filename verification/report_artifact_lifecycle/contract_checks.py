"""Policy and register checks for Slice 17.15."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.contract import (
    CONTRACT_RELATIVE,
    MAX_VERSIONS,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
    SLOTS,
)
from verification.report_artifact_lifecycle.helpers import add_check, read_json
from verification.report_artifact_lifecycle.models import CheckResult, Defect


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict[str, Any] = {}
    path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if not path.is_file():
        return checks, defects, policy

    policy = read_json(path)
    add_check(
        checks,
        defects,
        "policy:schema",
        policy.get("schema") == POLICY_SCHEMA,
        str(policy.get("schema")),
        "policy",
    )
    for key, expected in POLICY_REQUIRED_VALUES.items():
        actual = policy.get(key)
        add_check(
            checks,
            defects,
            f"policy:{key}",
            actual == expected,
            str(actual),
            "policy",
        )

    # Hard fail gates
    add_check(
        checks,
        defects,
        "policy:start_17_16_false",
        policy.get("start_slice_17_16") is True,
        str(policy.get("start_slice_17_16")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:data_lake_no_retention",
        policy.get("telemetry_data_lake_uses_report_retention") is False,
        str(policy.get("telemetry_data_lake_uses_report_retention")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:max_assessment_versions",
        policy.get("assessment_versions_per_repository", 99) <= MAX_VERSIONS,
        str(policy.get("assessment_versions_per_repository")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:max_eir_versions",
        policy.get("engineering_intelligence_versions_per_portfolio", 99) <= MAX_VERSIONS,
        str(policy.get("engineering_intelligence_versions_per_portfolio")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:run_ids_metadata_not_folder_authority",
        policy.get("run_ids_are_metadata") is True
        and policy.get("repository_folder_identity") == "human_readable_logical_repository",
        "run_ids_are_metadata + human_readable_logical_repository",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:slots_exact",
        list(policy.get("slots") or []) == list(SLOTS),
        str(policy.get("slots")),
        "policy",
    )

    add_check(
        checks,
        defects,
        "contract:exists",
        (monorepo / CONTRACT_RELATIVE).is_file(),
        CONTRACT_RELATIVE,
        "policy",
    )
    return checks, defects, policy


def check_register(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    register: dict[str, Any] = {}
    path = monorepo / REGISTER_RELATIVE
    add_check(checks, defects, "register:exists", path.is_file(), REGISTER_RELATIVE, "register")
    if not path.is_file():
        return checks, defects, register

    register = read_json(path)
    add_check(
        checks,
        defects,
        "register:schema",
        register.get("schema") == REGISTER_SCHEMA,
        str(register.get("schema")),
        "register",
    )
    entries = register.get("entries") or []
    add_check(checks, defects, "register:entries", bool(entries), str(len(entries)), "register")
    if entries:
        entry = entries[0]
        add_check(
            checks,
            defects,
            "register:repository_id_format",
            str(entry.get("repository_id", "")).startswith(("github-", "local-")),
            str(entry.get("repository_id")),
            "register",
        )
        add_check(
            checks,
            defects,
            "register:portfolio_id_human",
            bool(entry.get("portfolio_id")) and "portfolio-sv" not in str(entry.get("portfolio_id")),
            str(entry.get("portfolio_id")),
            "register",
        )
        add_check(
            checks,
            defects,
            "register:slots",
            list(entry.get("slots") or []) == list(SLOTS),
            str(entry.get("slots")),
            "register",
        )
    return checks, defects, register
