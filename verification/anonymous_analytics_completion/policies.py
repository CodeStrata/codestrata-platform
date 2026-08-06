"""Deterministic Epic 10 analytics policy URN registry (Slice 10.9)."""

from __future__ import annotations

from verification.anonymous_analytics_completion.inventory import (
    EngineAnalyticsInventory,
    VsCodeAnalyticsInventory,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect

POLICY_REGISTRY: tuple[str, ...] = tuple(
    sorted(
        {
            "community-anonymous-analytics-policy:1.0",
            "community-anonymous-installation-identity-policy:1.0",
            "community-runtime-analytics-policy:1.0",
            "community-assessment-analytics-policy:1.0",
            "community-repository-aggregate-analytics-policy:1.0",
            "community-ai-analytics-policy:1.0",
            "community-vscode-anonymous-analytics-policy:1.0",
        }
    )
)

EXPECTED_POLICY_COUNT = 7


def build_policy_registry() -> list[str]:
    return list(POLICY_REGISTRY)


def check_policies(
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    checks.append(
        CheckResult(
            name="policy:registry_count_7",
            ok=len(POLICY_REGISTRY) == EXPECTED_POLICY_COUNT,
            detail=f"count={len(POLICY_REGISTRY)}",
            category="policies",
        )
    )
    checks.append(
        CheckResult(
            name="policy:registry_sorted",
            ok=list(POLICY_REGISTRY) == sorted(POLICY_REGISTRY),
            category="policies",
        )
    )
    checks.append(
        CheckResult(
            name="policy:registry_unique",
            ok=len(POLICY_REGISTRY) == len(set(POLICY_REGISTRY)),
            category="policies",
        )
    )

    live = {
        "base": engine.base_policy_urn,
        "identity": engine.identity_policy_urn,
        "runtime": engine.runtime_policy_urn,
        "assessment": engine.assessment_policy_urn,
        "repository_aggregates": engine.repository_policy_urn,
        "ai": engine.ai_policy_urn,
        "vscode": vscode.policy_urn,
    }
    for key, urn in sorted(live.items()):
        ok = urn in POLICY_REGISTRY
        checks.append(
            CheckResult(
                name=f"policy:live_matches_registry:{key}",
                ok=ok,
                detail=urn,
                category="policies",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    "version registry defect",
                    key,
                    "member of policy registry",
                    urn or "missing",
                )
            )

    for urn in POLICY_REGISTRY:
        ok = urn.endswith(":1.0")
        checks.append(
            CheckResult(
                name=f"policy:version_1_0:{urn}",
                ok=ok,
                category="policies",
            )
        )
        if not ok:
            defects.append(Defect("version registry defect", urn, ":1.0", urn))

    return checks, defects
