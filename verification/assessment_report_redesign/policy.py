"""Policy checks."""

from __future__ import annotations

import json
from pathlib import Path

from verification.assessment_report_redesign.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
)
from verification.assessment_report_redesign.models import CheckResult, Defect


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    if not path.is_file():
        checks.append(
            CheckResult("policy:exists", False, "missing", "design_policy")
        )
        defects.append(
            Defect("harness defect", "policy", "present", "missing")
        )
        return checks, defects

    policy = json.loads(path.read_text(encoding="utf-8"))
    checks.append(
        CheckResult(
            "policy:id_version",
            policy.get("policy_id") == POLICY_ID
            and policy.get("policy_version") == POLICY_VERSION,
            f"{POLICY_ID}:{POLICY_VERSION}",
            "design_policy",
        )
    )
    required_true = (
        "assessment_truth_authoritative",
        "presentation_only",
        "local_only",
        "offline_capable",
        "responsive_required",
        "print_safe_required",
        "accessibility_baseline_required",
        "light_theme_default",
        "dark_theme_supported",
        "consumes_design_system_tokens",
    )
    for key in required_true:
        checks.append(
            CheckResult(
                f"policy:{key}",
                policy.get(key) is True,
                str(policy.get(key)),
                "design_policy",
            )
        )
    required_false = (
        "remote_assets_allowed",
        "remote_fonts_allowed",
        "external_scripts_allowed",
        "source_content_transmission_allowed",
        "token_duplication_allowed",
        "engineering_intelligence_report_redesign_allowed",
        "start_slice_14_4",
        "assessment_schema_bump_allowed",
        "scoring_changes_allowed",
    )
    for key in required_false:
        checks.append(
            CheckResult(
                f"policy:{key}",
                policy.get(key) is False,
                str(policy.get(key)),
                "design_policy",
            )
        )
    checks.append(
        CheckResult(
            "policy:schema_1_2",
            policy.get("assessment_schema_version") == "1.2",
            str(policy.get("assessment_schema_version")),
            "schema_boundary",
        )
    )
    checks.append(
        CheckResult(
            "policy:design_system_1_0",
            policy.get("design_system_version") == "1.0",
            str(policy.get("design_system_version")),
            "design_system",
        )
    )
    # No path/customer leakage in policy JSON keys/values beyond relative docs.
    text = path.read_text(encoding="utf-8")
    leak = any(x in text for x in ("/Users/", "file://", "timestamp", "C:\\\\"))
    checks.append(
        CheckResult("policy:no_path_leak", not leak, "clean", "design_policy")
    )
    return checks, defects
