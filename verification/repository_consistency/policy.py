"""Consistency policy checks."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.contract import (
    POLICY_RELATIVE,
    POLICY_SCHEMA,
)
from verification.repository_consistency.inventory import add_check, load_json
from verification.repository_consistency.models import CheckResult, Defect


def check_consistency_policy(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if not path.is_file():
        return checks, defects, {}
    policy = load_json(path)
    add_check(
        checks,
        defects,
        "policy:schema",
        policy.get("schema") == POLICY_SCHEMA,
        str(policy.get("schema")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:start_slice_16_8_true",
        policy.get("start_slice_16_8", False) is True,
        str(policy.get("start_slice_16_8", False)),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:start_slice_16_9_true",
        policy.get("start_slice_16_9", False) is True,
        str(policy.get("start_slice_16_9", False)),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:start_slice_16_10_true",
        policy.get("start_slice_16_10", False) is True,
        str(policy.get("start_slice_16_10", False)),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:start_epic_17_true",
        policy.get("start_epic_17", False) is True,
        str(policy.get("start_epic_17", False)),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:start_slice_17_2_true",
        policy.get("start_slice_17_2", False) is True,
        str(policy.get("start_slice_17_2", False)),
        "policy",
        classification="slice_17_4_started",
    )
    for key in (
        "authoritative_source_resolution",
        "version_consistency",
        "public_private_scope_consistency",
        "source_generated_consistency",
        "build_authority_consistency",
        "policy_contract_uniqueness",
        "design_brand_uniqueness",
        "historical_isolation",
        "no_release_publish_deploy",
        "no_remote_creation",
        "no_cutover",
    ):
        add_check(
            checks,
            defects,
            f"policy:field:{key}",
            bool(policy.get(key)),
            key,
            "policy",
        )
    add_check(
        checks,
        defects,
        "policy:production_ingestion_false",
        policy.get("production_ingestion_enabled", True) is False,
        str(policy.get("production_ingestion_enabled")),
        "policy",
    )
    mirror = monorepo / "insights/policies/repository_consistency_policy.json"
    if mirror.is_file():
        auth = path.read_bytes()
        mir = mirror.read_bytes()
        add_check(
            checks,
            defects,
            "policy:insights_mirror_byte_identical",
            auth == mir,
            "insights/policies/repository_consistency_policy.json",
            "policy",
        )
    else:
        add_check(
            checks,
            defects,
            "policy:insights_mirror_byte_identical",
            False,
            "missing_insights_mirror",
            "policy",
        )
    return checks, defects, policy
