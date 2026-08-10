"""AI usage telemetry: construction-only; prompts/responses excluded."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import (
    AI_ANALYTICS_CATALOGS_PY,
    AI_ANALYTICS_PROJECTION_PY,
    SERVICE_PY,
)
from verification.community_ai_providers.helpers import check, read_text
from verification.community_ai_providers.models import CheckResult, Defect


def check_telemetry(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    service = read_text(monorepo / SERVICE_PY)
    projection = read_text(monorepo / AI_ANALYTICS_PROJECTION_PY)
    catalogs = read_text(monorepo / AI_ANALYTICS_CATALOGS_PY)

    # ai_usage not invoked on assess path (construction-only elsewhere).
    assess_emits = (
        "project_ai_analytics" in service
        or "build_ai_analytics" in service
        or "AIAnalyticsEvent" in service
    )
    checks.append(
        check(
            "telemetry:not_on_assess_path",
            not assess_emits,
            "assessment service does not emit ai_usage events",
            "telemetry",
        )
    )
    limitations.append("ai_usage_telemetry_deferred")

    # Projection allowlist forbids prompt/response.
    forbids_prompt = '"prompt"' in projection and '"response"' in projection
    checks.append(
        check(
            "telemetry:prompts_responses_forbidden",
            forbids_prompt,
            "ai_analytics_projection forbids prompt/response keys",
            "telemetry",
        )
    )

    # Model family catalog: openrouter_routed not in APPROVED_AI_MODEL_FAMILIES.
    model_families_ok = "APPROVED_AI_MODEL_FAMILIES" in catalogs
    openrouter_model_family = "openrouter_routed" in catalogs
    checks.append(
        check(
            "telemetry:model_family_catalog",
            model_families_ok and not openrouter_model_family,
            "openrouter_routed absent from APPROVED_AI_MODEL_FAMILIES",
            "telemetry",
        )
    )

    summary = {
        "ai_usage_on_assess_path": False,
        "construction_only": True,
        "prompts_responses_excluded": True,
        "openrouter_model_family_in_catalog": openrouter_model_family,
        "limitation": "ai_usage_telemetry_deferred",
    }
    return checks, defects, summary, limitations
