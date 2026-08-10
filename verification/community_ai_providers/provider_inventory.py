"""Discover AssessAIProviderRegistry registration of three providers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import (
    ASSESS_AI_PY,
    FACTORY_PY,
    SUPPORTED_PROVIDERS,
)
from verification.community_ai_providers.helpers import check, hard_defect, read_text
from verification.community_ai_providers.models import CheckResult, Defect


def check_provider_inventory(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    assess_ai = read_text(monorepo / ASSESS_AI_PY)
    factory = read_text(monorepo / FACTORY_PY)

    has_registry = "class AssessAIProviderRegistry" in assess_ai
    checks.append(
        check(
            "inventory:registry_class",
            has_registry,
            "AssessAIProviderRegistry present",
            "provider_inventory",
        )
    )
    if not has_registry:
        defects.append(
            hard_defect(
                "missing_registry",
                "inventory:registry_class",
                "present",
                "absent",
            )
        )

    registered: list[str] = []
    for name in SUPPORTED_PROVIDERS:
        ok = f'registry.register("{name}"' in assess_ai
        checks.append(
            check(
                f"inventory:register_{name}",
                ok,
                f"register({name})",
                "provider_inventory",
            )
        )
        if ok:
            registered.append(name)
        else:
            defects.append(
                hard_defect(
                    "missing_provider_registration",
                    f"inventory:register_{name}",
                    "registered",
                    "absent",
                )
            )

    factory_ok = (
        "def create_assess_ai_provider" in factory
        and 'SUPPORTED_ASSESS_AI_PROVIDERS = frozenset({"bedrock", "openai", "openrouter"})'
        in factory
    )
    checks.append(
        check(
            "inventory:factory_supported",
            factory_ok,
            "create_assess_ai_provider + SUPPORTED_ASSESS_AI_PROVIDERS",
            "provider_inventory",
        )
    )
    if not factory_ok:
        defects.append(
            hard_defect(
                "factory_drift",
                "inventory:factory_supported",
                "bedrock|openai|openrouter",
                "mismatch",
            )
        )

    adapter_paths = {
        "bedrock": monorepo / "engine/src/codestrata/ai/providers/bedrock.py",
        "openai": monorepo / "engine/src/codestrata/ai/providers/openai_provider.py",
        "openrouter": monorepo
        / "engine/src/codestrata/ai/providers/openrouter_provider.py",
    }
    for name, path in adapter_paths.items():
        ok = path.is_file()
        checks.append(
            check(
                f"inventory:adapter_{name}",
                ok,
                str(path.relative_to(monorepo)),
                "provider_inventory",
            )
        )
        if not ok:
            defects.append(
                hard_defect(
                    "missing_adapter",
                    f"inventory:adapter_{name}",
                    "present",
                    "absent",
                )
            )

    summary = {
        "registry": "AssessAIProviderRegistry",
        "registered": registered,
        "supported_constant": list(SUPPORTED_PROVIDERS),
        "factory": "create_assess_ai_provider",
        "cross_provider_fallback": False,
    }
    return checks, defects, summary
