"""Registry determinism checks (Slice 10.9 completion).

Full end-to-end report determinism (two full runs producing byte-identical
JSON) is validated in ``tests/verification/anonymous_analytics_completion``.
This module checks that the deterministic building blocks — the policy and
schema registries — are stable within a single process.
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_completion.policies import build_policy_registry
from verification.anonymous_analytics_completion.schemas import build_schema_registry


def check_determinism(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    a = build_policy_registry()
    b = build_policy_registry()
    checks.append(
        CheckResult(
            "determinism:policy_registry_stable",
            ok=a == b,
            category="determinism",
        )
    )

    s1 = build_schema_registry()
    s2 = build_schema_registry()
    checks.append(
        CheckResult(
            "determinism:schema_registry_stable",
            ok=s1 == s2,
            category="determinism",
        )
    )

    _ = monorepo
    for item in checks:
        if not item.ok:
            defects.append(Defect("harness defect", item.name, "pass", "fail"))
    return checks, defects
