"""OpenRouter provider E2E or OWNER_CREDENTIAL_REQUIRED soft validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.helpers import (
    check,
    contains,
    env_present,
    artifact_dir,
)
from verification.community_ai_providers.models import CheckResult, Defect


def check_openrouter(
    monorepo: Path,
    *,
    repositories: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    key_present = env_present("OPENROUTER_API_KEY")
    factory = monorepo / "engine/src/codestrata/ai/providers/factory.py"
    provider = monorepo / "engine/src/codestrata/ai/providers/openrouter_provider.py"
    doctor = monorepo / "engine/src/codestrata/ai/providers/doctor.py"
    assess_ai = monorepo / "engine/src/codestrata/extensions/assess_ai.py"

    arch_ok = (
        factory.is_file()
        and contains(factory, "openrouter")
        and provider.is_file()
        and doctor.is_file()
        and contains(assess_ai, 'registry.register("openrouter"')
    )
    checks.append(
        check(
            "openrouter:architecture",
            arch_ok,
            "factory+adapter+doctor+registry",
            "openrouter",
        )
    )

    e2e_artifacts: list[str] = []
    for item in repositories.get("selected") or []:
        work = artifact_dir(item, "work_openrouter", monorepo=monorepo)
        if work and (
            (work / "advisor.json").is_file()
            or (work / "assessment.json").is_file()
        ):
            e2e_artifacts.append(str(item.get("catalog_id")))

    if key_present and e2e_artifacts:
        e2e_status = "passed"
        detail = f"artifacts={e2e_artifacts}"
        ok = True
    elif key_present:
        e2e_status = "architecture_validated_live_optional"
        detail = "OPENROUTER_API_KEY present; no /tmp assess-out/openrouter artifacts"
        ok = arch_ok
        limitations.append("provider_latency_cost_variance")
    else:
        e2e_status = "OWNER_CREDENTIAL_REQUIRED"
        detail = "OPENROUTER_API_KEY absent; architecture validated"
        ok = arch_ok
        limitations.append("owner_credential_required_openrouter")

    checks.append(
        check(
            "openrouter:e2e_or_soft",
            ok,
            f"status={e2e_status}; {detail}",
            "openrouter",
        )
    )

    summary = {
        "credential_present": key_present,
        "architecture_validated": arch_ok,
        "e2e_status": e2e_status,
        "e2e_artifacts": e2e_artifacts,
        "values_logged": False,
    }
    return checks, defects, summary, limitations
