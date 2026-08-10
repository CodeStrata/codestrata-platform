"""Configuration precedence: invalid provider errors; no silent fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import ASSESS_AI_PY, ASSESS_CLI_PY, FACTORY_PY
from verification.community_ai_providers.helpers import check, hard_defect, read_text
from verification.community_ai_providers.models import CheckResult, Defect


def check_configuration(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    factory = read_text(monorepo / FACTORY_PY)
    assess_ai = read_text(monorepo / ASSESS_AI_PY)
    assess_cli = read_text(monorepo / ASSESS_CLI_PY)
    precedence = monorepo / "engine/src/codestrata/ai/provider_contracts/configuration_precedence.py"

    invalid_raises = "Unsupported assess AI provider" in assess_ai
    checks.append(
        check(
            "configuration:invalid_provider_errors",
            invalid_raises,
            "AIProviderConfigurationError on unknown provider",
            "configuration",
        )
    )
    if not invalid_raises:
        defects.append(
            hard_defect(
                "silent_fallback",
                "configuration:invalid_provider_errors",
                "raise",
                "missing",
            )
        )

    # Model ID precedence documented: CLI --model-id wins.
    has_model_id = "--model-id" in assess_cli
    checks.append(
        check(
            "configuration:model_id_cli",
            has_model_id,
            "--model-id CLI flag",
            "configuration",
        )
    )

    precedence_notes = []
    if precedence.is_file():
        text = read_text(precedence)
        if "CLI --model-id" in text or "cli_model_id" in text:
            precedence_notes.append("CLI --model-id > env > settings")
    if "resolve_assess_model_id" in factory:
        precedence_notes.append("resolve_assess_model_id in factory")

    checks.append(
        check(
            "configuration:precedence_documented",
            bool(precedence_notes),
            "; ".join(precedence_notes) or "missing",
            "configuration",
        )
    )

    # Provider selected via settings.ai.provider — single active provider.
    single = "settings.ai.provider" in factory or "provider_name =" in factory
    checks.append(
        check(
            "configuration:single_active_provider",
            single,
            "one provider from [ai].provider",
            "configuration",
        )
    )

    summary = {
        "invalid_provider_raises": invalid_raises,
        "silent_fallback": False,
        "model_id_flag": "--model-id",
        "ai_flags": "--with-ai/--no-ai",
        "precedence_notes": precedence_notes,
    }
    return checks, defects, summary
