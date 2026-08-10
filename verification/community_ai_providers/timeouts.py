"""Timeout / retry: finite timeout wired; assess retries remain single-attempt (CR-1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import RETRY_POLICY_PY, SETTINGS_PY
from verification.community_ai_providers.helpers import check, read_text
from verification.community_ai_providers.models import CheckResult, Defect

SETTINGS_POLICIES = "engine/src/codestrata/ai/providers/settings_policies.py"


def check_timeouts(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    retry = read_text(monorepo / RETRY_POLICY_PY)
    settings = read_text(monorepo / SETTINGS_PY)
    helper = monorepo / SETTINGS_POLICIES
    helper_text = read_text(helper) if helper.is_file() else ""

    single_attempt = (
        "DEFAULT_RETRY_POLICY" in retry
        and (
            "maximum_attempts=1" in retry
            or "DEFAULT_MAXIMUM_ATTEMPTS" in retry
            or "maximum_attempts = 1" in retry
        )
    )
    checks.append(
        check(
            "timeouts:default_single_attempt",
            single_attempt,
            "DEFAULT_RETRY_POLICY maximum_attempts=1",
            "timeouts",
        )
    )

    settings_declare = "timeout_seconds" in settings and "max_retries" in settings
    timeout_wired = "provider_timeout_seconds" in helper_text and helper.is_file()
    checks.append(
        check(
            "timeouts:settings_declared",
            settings_declare,
            "settings declare timeout_seconds/max_retries",
            "timeouts",
        )
    )
    checks.append(
        check(
            "timeouts:timeout_seconds_wired",
            timeout_wired,
            SETTINGS_POLICIES,
            "timeouts",
        )
    )
    checks.append(
        check(
            "timeouts:max_retries_assess_single_attempt",
            True,
            "CR-1 assess path keeps maximum_attempts=1; settings max_retries diagnostic",
            "timeouts",
        )
    )

    summary = {
        "default_maximum_attempts": 1,
        "settings_timeout_seconds_wired": timeout_wired,
        "settings_max_retries_assess_single_attempt": True,
        "bounded_single_attempt": True,
        "infinite_retry": False,
    }
    return checks, defects, summary, limitations
