"""Documentation consistency checks (Slice 10.9 completion).

Reuses Slice 10.8's ``check_documentation`` and additionally confirms the
required soft-mentions of Epic 10 completion verification exist across
adjacent documentation, without claiming production analytics collection.
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.inventory import adapt_checks
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.documentation import (
    check_documentation as _check_documentation_108,
)

_SOFT_MENTION_DOCS: tuple[str, ...] = (
    "ARCHITECTURE.md",
    "engine/docs/telemetry.md",
    "engine/PRIVACY.md",
    "engine/README.md",
    "vscode-plugin/docs/analytics.md",
    "verification/anonymous_analytics_privacy/README.md",
)

_SOFT_MENTION_NEEDLES: tuple[str, ...] = ("10.9", "sv10-9", "completion verification")

_FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "analytics is collected in production",
    "analytics collection is enabled",
    "epic 10 is operational",
)


def check_documentation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    raw_checks, raw_defects = _check_documentation_108(monorepo)
    checks, defects = adapt_checks(raw_checks, raw_defects)

    for rel in _SOFT_MENTION_DOCS:
        path = monorepo / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        lowered = text.lower()
        ok = path.is_file() and any(n.lower() in lowered for n in _SOFT_MENTION_NEEDLES)
        checks.append(
            CheckResult(
                f"docs:mentions_slice_10_9:{rel}",
                ok=ok,
                detail=rel,
                category="documentation",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    "documentation inconsistency",
                    rel,
                    "mentions Slice 10.9 / completion verification",
                    "missing",
                )
            )

    completion_readme = (
        monorepo / "verification" / "anonymous_analytics_completion" / "README.md"
    )
    checks.append(
        CheckResult(
            "docs:completion_readme_present",
            ok=completion_readme.is_file(),
            category="documentation",
        )
    )

    for rel in _SOFT_MENTION_DOCS:
        path = monorepo / rel
        if not path.is_file():
            continue
        lowered = path.read_text(encoding="utf-8").lower()
        for claim in _FORBIDDEN_CLAIMS:
            bad = claim in lowered
            checks.append(
                CheckResult(
                    f"docs:no_false_claim:{rel}:{claim[:24]}",
                    ok=not bad,
                    category="documentation",
                )
            )
            if bad:
                defects.append(
                    Defect(
                        "documentation inconsistency",
                        rel,
                        "no production-operational claim",
                        claim,
                    )
                )

    return checks, defects
