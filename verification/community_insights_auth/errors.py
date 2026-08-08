"""Auth error code checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, ensure_platform_importable
from verification.community_insights_auth.contract import AUTH_PACKAGE
from verification.community_insights_auth.inventory import load_json, read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_errors(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, "platform/policies/community_insights_auth_policy.json")
    errors_py = read_text(monorepo, f"{AUTH_PACKAGE}/errors.py")

    expected = set(policy.get("error_codes") or [])
    add_check(
        checks,
        defects,
        "errors:policy_codes_present",
        bool(expected),
        "present",
        "platform",
    )

    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights_auth.errors import (
        INSIGHTS_AUTH_ERROR_CODES,
        SAFE_MESSAGES,
    )

    add_check(
        checks,
        defects,
        "errors:bounded_codes",
        INSIGHTS_AUTH_ERROR_CODES == expected,
        "matched",
        "platform",
    )
    add_check(
        checks,
        defects,
        "errors:safe_messages",
        len(SAFE_MESSAGES) == len(INSIGHTS_AUTH_ERROR_CODES)
        and "aws" not in " ".join(SAFE_MESSAGES.values()).lower(),
        "generic",
        "platform",
    )
    add_check(
        checks,
        defects,
        "errors:bounded_source",
        "SAFE_MESSAGES" in errors_py and "INSIGHTS_AUTH_ERROR_CODES" in errors_py,
        "bounded",
        "platform",
    )
    return checks, defects
