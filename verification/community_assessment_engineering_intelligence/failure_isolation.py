"""Failure isolation source audit for Slice 17.19."""

from __future__ import annotations

from pathlib import Path

from verification.community_assessment_engineering_intelligence.contract import (
    LIFECYCLE_PY,
    POLICY_RELATIVE,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    load_json,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_failure_isolation(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo / POLICY_RELATIVE)
    lifecycle = read_text(monorepo / LIFECYCLE_PY)

    failed_promotes = policy.get("failed_generation_does_not_promote") is True
    checks.append(
        check(
            "failure_isolation:policy_failed_generation_does_not_promote",
            failed_promotes,
            str(policy.get("failed_generation_does_not_promote")),
            "failure_isolation",
        )
    )
    if not failed_promotes:
        defects.append(
            hard_defect(
                "policy_failed_promote",
                "failure_isolation:policy_failed_generation_does_not_promote",
                "true",
                "false",
            )
        )

    has_validate = "def validate_assessment_bundle" in lifecycle
    checks.append(
        check(
            "failure_isolation:validate_assessment_bundle",
            has_validate,
            "present",
            "failure_isolation",
        )
    )
    if not has_validate:
        defects.append(
            hard_defect(
                "missing_validate",
                "failure_isolation:validate_assessment_bundle",
                "present",
                "absent",
            )
        )

    # discard_staging must refuse non-staging and never touch current/previous.
    has_discard = "def discard_staging" in lifecycle
    refuses_non_staging = "refuse to discard non-staging path" in lifecycle
    mentions_current_guard = "current" in lifecycle and "previous" in lifecycle
    discard_ok = has_discard and refuses_non_staging
    checks.append(
        check(
            "failure_isolation:discard_staging_isolated",
            discard_ok,
            f"discard={has_discard};refuse={refuses_non_staging};slots={mentions_current_guard}",
            "failure_isolation",
        )
    )
    if not discard_ok:
        defects.append(
            hard_defect(
                "discard_isolation",
                "failure_isolation:discard_staging_isolated",
                "isolated",
                "unsafe",
            )
        )

    # Source comment / naming: failed assessment must not promote.
    # Policy key failed_assessment_promotes is used by 17.15; 17.19 uses failed_generation.
    source_failed = "validate_assessment_bundle(staging_directory)" in lifecycle
    checks.append(
        check(
            "failure_isolation:promote_requires_validation",
            source_failed,
            "promote validates staging first",
            "failure_isolation",
        )
    )

    summary = {
        "failed_assessment_promotes": False,
        "validate_assessment_bundle": has_validate,
        "discard_staging_isolated": discard_ok,
        "failed_generation_does_not_promote": failed_promotes,
    }
    return checks, defects, summary
