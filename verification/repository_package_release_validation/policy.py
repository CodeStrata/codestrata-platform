"""Policy and contract presence checks."""

from __future__ import annotations

from pathlib import Path

from verification.repository_package_release_validation.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
)
from verification.repository_package_release_validation.helpers import add_check, load_json
from verification.repository_package_release_validation.models import CheckResult, Defect


def check_policy(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if not path.is_file():
        return checks, defects, {}
    policy = load_json(path)
    add_check(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
    add_check(
        checks,
        defects,
        "policy:start_slice_16_9_true",
        policy.get("start_slice_16_9", False) is True,
        str(policy.get("start_slice_16_9")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:start_slice_16_10_true",
        policy.get("start_slice_16_10", False) is True,
        str(policy.get("start_slice_16_10")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:start_epic_17_false",
        policy.get("start_epic_17", False) is False,
        str(policy.get("start_epic_17", False)),
        "policy",
        classification="epic_17_started",
    )
    for key in ("no_publish", "no_deploy", "no_tag", "no_commit", "no_marketplace_publish", "no_pypi_publish"):
        add_check(checks, defects, f"policy:{key}", policy.get(key) is True, str(policy.get(key)), "policy")
    add_check(
        checks,
        defects,
        "policy:production_ingestion_false",
        policy.get("production_ingestion_enabled", True) is False,
        str(policy.get("production_ingestion_enabled")),
        "policy",
    )
    mirror = monorepo / "insights/policies/repository_package_release_validation_policy.json"
    add_check(
        checks,
        defects,
        "policy:insights_mirror_identical",
        mirror.is_file() and mirror.read_bytes() == path.read_bytes(),
        "insights mirror",
        "policy",
    )
    cpath = monorepo / CONTRACT_RELATIVE
    add_check(checks, defects, "contract:exists", cpath.is_file(), CONTRACT_RELATIVE, "policy")
    if cpath.is_file():
        cdata = load_json(cpath)
        add_check(
            checks,
            defects,
            "contract:schema",
            cdata.get("schema") == "repository-package-release-validation-verification:1.0.0",
            str(cdata.get("schema")),
            "policy",
        )
    return checks, defects, policy
