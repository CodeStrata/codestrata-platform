"""Evidence and policy loading for Slice 17.13."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    RESULT_REGISTER_RELATIVE,
    RESULT_REGISTER_SCHEMA,
    SUITE_REGISTER_RELATIVE,
    SUITE_REGISTER_SCHEMA,
)
from verification.community_22_repository_validation.helpers import add_check, read_json
from verification.community_22_repository_validation.models import CheckResult, Defect


def load_evidence(monorepo: Path) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for rel in (
        POLICY_RELATIVE,
        SUITE_REGISTER_RELATIVE,
        RESULT_REGISTER_RELATIVE,
        CONTRACT_RELATIVE,
    ):
        path = monorepo / rel
        if path.is_file():
            evidence[rel] = read_json(path)
    return evidence


def check_policy_evidence(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict[str, Any] = {}
    suite_register: dict[str, Any] = {}

    policy_path = monorepo / POLICY_RELATIVE
    add_check(
        checks,
        defects,
        "policy:exists",
        policy_path.is_file(),
        POLICY_RELATIVE,
        "policy",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if policy_path.is_file():
        policy = read_json(policy_path)
        add_check(
            checks,
            defects,
            "policy:schema",
            policy.get("schema") == POLICY_SCHEMA,
            str(policy.get("schema")),
            "policy",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        add_check(
            checks,
            defects,
            "policy:individual_reports",
            policy.get("individual_assessment_reports") is True,
            "true",
            "policy",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        add_check(
            checks,
            defects,
            "policy:insights_validation",
            policy.get("insights_validation") is True,
            "true",
            "policy",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        add_check(
            checks,
            defects,
            "policy:telemetry_validation",
            policy.get("telemetry_validation_enabled") is True,
            "true",
            "policy",
            CheckResult=CheckResult,
            Defect=Defect,
        )

    suite_path = monorepo / SUITE_REGISTER_RELATIVE
    if suite_path.is_file():
        suite_register = read_json(suite_path)
        add_check(
            checks,
            defects,
            "suite_register:schema",
            suite_register.get("schema") == SUITE_REGISTER_SCHEMA,
            str(suite_register.get("schema")),
            "policy",
            CheckResult=CheckResult,
            Defect=Defect,
        )

    result_path = monorepo / RESULT_REGISTER_RELATIVE
    if result_path.is_file():
        result_register = read_json(result_path)
        add_check(
            checks,
            defects,
            "result_register:schema",
            result_register.get("schema") == RESULT_REGISTER_SCHEMA,
            str(result_register.get("schema")),
            "policy",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        safe_fields = result_register.get("safe_fields") or []
        add_check(
            checks,
            defects,
            "result_register:safe_fields",
            "repository_validation_id" in safe_fields and "limitations" in safe_fields,
            str(safe_fields),
            "policy",
            CheckResult=CheckResult,
            Defect=Defect,
        )

    return checks, defects, policy, suite_register
