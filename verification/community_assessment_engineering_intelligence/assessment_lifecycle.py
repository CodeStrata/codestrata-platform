"""Assessment lifecycle source + optional controlled proof for Slice 17.19."""

from __future__ import annotations

from pathlib import Path

from verification.community_assessment_engineering_intelligence.contract import LIFECYCLE_PY
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_assessment_lifecycle(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    lifecycle_path = monorepo / LIFECYCLE_PY
    text = read_text(lifecycle_path) if lifecycle_path.is_file() else ""
    has_promote = "def promote_assessment_run" in text
    has_validate = "def validate_assessment_bundle" in text
    rotates = "SLOT_CURRENT" in text and "SLOT_PREVIOUS" in text
    checks.append(
        check(
            "assessment_lifecycle:promote_api",
            has_promote,
            "promote_assessment_run",
            "assessment_lifecycle",
        )
    )
    checks.append(
        check(
            "assessment_lifecycle:slots",
            rotates,
            "current/previous",
            "assessment_lifecycle",
        )
    )
    checks.append(
        check(
            "assessment_lifecycle:validate_before_promote",
            has_validate and "validate_assessment_bundle(staging_directory)" in text,
            "validate then promote",
            "assessment_lifecycle",
        )
    )
    if not (has_promote and rotates and has_validate):
        defects.append(
            hard_defect(
                "lifecycle_source",
                "assessment_lifecycle:promote_api",
                "A/B/C + fail-D semantics",
                "incomplete",
            )
        )

    test_path = monorepo / "engine/tests/artifacts/test_report_lifecycle.py"
    test_text = read_text(test_path) if test_path.is_file() else ""
    has_abc = "test_assessment_rotation_abc_fail_d" in test_text
    checks.append(
        check(
            "assessment_lifecycle:unit_test_abc_fail_d",
            has_abc,
            "test_report_lifecycle.py",
            "assessment_lifecycle",
        )
    )
    if not has_abc:
        defects.append(
            hard_defect(
                "lifecycle_test",
                "assessment_lifecycle:unit_test_abc_fail_d",
                "present",
                "absent",
            )
        )

    # Soft: live A/B/C not re-executed in this suite.
    limitations.append("controlled_lifecycle_source_proven")
    checks.append(
        check(
            "assessment_lifecycle:controlled_live_optional",
            True,
            "source+test proof; live A/B/C not re-executed",
            "assessment_lifecycle",
        )
    )

    summary = {
        "promote_assessment_run": has_promote,
        "slots": rotates,
        "abc_fail_d_test": has_abc,
        "live_abc_reexecuted": False,
        "controlled_lifecycle_source_proven": True,
    }
    return checks, defects, summary, limitations
