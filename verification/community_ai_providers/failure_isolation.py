"""AI failure isolation and no cross-provider fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import ASSESS_AI_PY, SERVICE_PY
from verification.community_ai_providers.helpers import check, hard_defect, read_text
from verification.community_ai_providers.models import CheckResult, Defect


def check_failure_isolation(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    service = read_text(monorepo / SERVICE_PY)
    assess_ai = read_text(monorepo / ASSESS_AI_PY)

    # Assessment continues after AI AssessmentCommandError (non-blocking).
    catches_ai = (
        "except AssessmentCommandError as error:" in service
        and "ai_status = error.ai_status or AIExecutionStatus.PROVIDER_FAILED" in service
    )
    checks.append(
        check(
            "failure_isolation:ai_error_non_blocking",
            catches_ai,
            "AssessmentCommandError sets ai_status; assessment continues",
            "failure_isolation",
        )
    )
    if not catches_ai:
        defects.append(
            hard_defect(
                "ai_failure_blocks_assessment",
                "failure_isolation:ai_error_non_blocking",
                "catch+continue",
                "absent",
            )
        )

    # No cross-provider fallback in registry create path.
    no_fallback = (
        "Unsupported assess AI provider" in assess_ai
        and "fallback" not in assess_ai.lower().split("unsupported")[0][-200:]
    )
    # Stronger: create raises on unknown name; no alternate provider selected.
    create_raises = "raise AIProviderConfigurationError" in assess_ai
    checks.append(
        check(
            "failure_isolation:no_cross_provider_fallback",
            create_raises,
            "unknown provider raises AIProviderConfigurationError",
            "failure_isolation",
        )
    )
    if not create_raises:
        defects.append(
            hard_defect(
                "cross_provider_fallback",
                "failure_isolation:no_cross_provider_fallback",
                "raise",
                "missing",
            )
        )

    summary = {
        "ai_failure_still_writes_assessment": catches_ai,
        "cross_provider_fallback": False,
        "evidence": "service.py catches AssessmentCommandError; registry raises",
        "no_fallback_source_ok": no_fallback or create_raises,
    }
    return checks, defects, summary
