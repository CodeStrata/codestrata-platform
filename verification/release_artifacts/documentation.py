"""Documentation overclaim and stale version scans."""

from __future__ import annotations

import re
from pathlib import Path

from verification.release_artifacts.contract import INTENDED_RELEASE_VERSION
from verification.release_artifacts.models import CheckResult, Defect, Warning

_README_PATHS = (
    "README.md",
    "engine/README.md",
    "engine/docs/installation.md",
    "platform/README.md",
)

_DANGEROUS_CLAIMS: tuple[tuple[str, str], ...] = (
    ("data_lake_claimed", r"(?i)(?<!no )(?<!without a )(?<!without )\bData Lake\b(?!.*(not|unavailable|deferred))"),
    ("openrouter_claimed", r"(?i)\bOpenRouter\b(?!.*(not|unsupported|deferred|not yet))"),
    ("distributed_rate", r"(?i)\bdistributed rate[- ]limit"),
    ("thirty_repositories", r"\b30 repositories\b"),
    ("nineteen_of_twenty_two", r"\b19/22\b"),
    ("industry_benchmark_claim", r"(?i)\bas an industry benchmark\b|\bindustry[- ]leading benchmark\b"),
)

_STALE_ENGINE_VERSION = re.compile(r"(?:Engine|codestrata)\s*[=:]?\s*0\.1\.0", re.IGNORECASE)


def check_documentation(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[Warning]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    warnings: list[Warning] = []

    for relative in _README_PATHS:
        path = monorepo / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for code, pattern in _DANGEROUS_CLAIMS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                warnings.append(
                    Warning(
                        code=f"doc_overclaim_{code}",
                        detail=f"{relative}: matched {code}",
                        release_impact="review",
                    )
                )
        if _STALE_ENGINE_VERSION.search(text):
            warnings.append(
                Warning(
                    code="stale_engine_version_in_docs",
                    detail=f"{relative}: references Engine 0.1.0; intended {INTENDED_RELEASE_VERSION}",
                )
            )

    checks.append(
        CheckResult(
            name="documentation:scanned_key_readmes",
            ok=True,
            detail=f"files={len(_README_PATHS)} warnings={len(warnings)}",
            category="documentation",
        )
    )

    blocking = [w for w in warnings if w.release_impact == "blocking"]
    for warning in blocking:
        defects.append(
            Defect(
                classification="documentation_overclaim",
                component="documentation",
                expected="no product overclaims",
                actual=warning.detail,
                release_impact="blocking",
            )
        )

    return checks, defects, warnings
