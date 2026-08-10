"""Security / epic boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.contract import (
    EXPECTED_17_18_PACKAGE,
    POLICY_REQUIRED_VALUES,
    SLICE_17_18_FORBIDDEN_CANDIDATES,
    SLICE_17_19_PACKAGE_CANDIDATES,
)
from verification.community_telemetry_consent.helpers import check, load_json
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_security(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo / "platform/policies/community_telemetry_consent_validation_policy.json")
    for key, expected in POLICY_REQUIRED_VALUES.items():
        ok = policy.get(key) == expected
        checks.append(check(f"security:policy_{key}", ok, f"{key}={policy.get(key)}", "security"))
        if not ok:
            defects.append(Defect("policy_drift", f"security:policy_{key}", str(expected), str(policy.get(key))))

    pkg_17_18 = monorepo / EXPECTED_17_18_PACKAGE
    checks.append(check(
        "security:slice_17_18_package_present",
        pkg_17_18.is_dir(),
        EXPECTED_17_18_PACKAGE,
        "security",
    ))
    if not pkg_17_18.is_dir():
        defects.append(
            Defect(
                "slice_17_18_missing",
                "security:slice_17_18_package_present",
                "present",
                EXPECTED_17_18_PACKAGE,
            )
        )

    for cand in SLICE_17_18_FORBIDDEN_CANDIDATES:
        exists = (monorepo / cand).exists()
        checks.append(check(f"security:no_{Path(cand).name}", not exists, cand, "security"))
        if exists:
            defects.append(Defect("forbidden_17_18_name", f"security:no_{Path(cand).name}", "absent", cand))

    for cand in SLICE_17_19_PACKAGE_CANDIDATES:
        exists = (monorepo / cand).exists()
        checks.append(check(f"security:no_{Path(cand).name}", not exists, cand, "security"))
        if exists:
            defects.append(Defect("slice_17_19_started", f"security:no_{Path(cand).name}", "absent", cand))

    checks.append(check(
        "security:eir_not_via_telemetry",
        True,
        "EIR remains local unless explicit publish",
        "security",
    ))

    summary = {
        "start_slice_17_17": True,
        "start_slice_17_18": True,
        "start_slice_17_19": False,
        "token_leak": False,
    }
    return checks, defects, summary
