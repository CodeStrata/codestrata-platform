"""Security / epic boundary for Slice 17.19 (17.20 allowed; 17.21 forbidden)."""

from __future__ import annotations

from pathlib import Path

from verification.community_assessment_engineering_intelligence.contract import (
    EXPECTED_17_20_PACKAGE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    SLICE_17_21_PACKAGE_CANDIDATES,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    load_json,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_security(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo / POLICY_RELATIVE)

    for key, expected in POLICY_REQUIRED_VALUES.items():
        ok = policy.get(key) == expected
        checks.append(
            check(f"security:policy_{key}", ok, f"{key}={policy.get(key)}", "security")
        )
        if not ok:
            defects.append(
                Defect(
                    "policy_drift",
                    f"security:policy_{key}",
                    str(expected),
                    str(policy.get(key)),
                )
            )

    start_20 = policy.get("start_slice_17_20") is True
    start_21 = policy.get("start_slice_17_21") is True if "start_slice_17_21" in policy else False
    checks.append(
        check("security:start_slice_17_20_true", start_20, "true", "security")
    )
    if not start_20:
        defects.append(
            hard_defect(
                "slice_17_20_not_enabled",
                "security:start_slice_17_20_true",
                "true",
                "false",
            )
        )

    expected_pkg = monorepo / EXPECTED_17_20_PACKAGE
    checks.append(
        check(
            "security:expected_17_20_package",
            expected_pkg.is_dir(),
            EXPECTED_17_20_PACKAGE,
            "security",
        )
    )
    if not expected_pkg.is_dir():
        defects.append(
            hard_defect(
                "missing_17_20_package",
                "security:expected_17_20_package",
                "present",
                "absent",
            )
        )

    for cand in SLICE_17_21_PACKAGE_CANDIDATES:
        exists = (monorepo / cand).exists()
        checks.append(
            check(f"security:no_{Path(cand).name}", not exists, cand, "security")
        )
        if exists:
            defects.append(
                hard_defect(
                    "slice_17_21_package",
                    f"security:no_{Path(cand).name}",
                    "absent",
                    cand,
                )
            )

    summary = {
        "start_slice_17_19": True,
        "start_slice_17_20": True,
        "start_slice_17_21": False,
        "slice_17_21_started": start_21,
    }
    return checks, defects, summary
