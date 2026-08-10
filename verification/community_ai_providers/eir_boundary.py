"""EIR does not invoke AI providers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.helpers import check, read_text
from verification.community_ai_providers.models import CheckResult, Defect


def check_eir_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = ["eir_provider_enrichment_deferred"]

    candidates = [
        monorepo / "engine/src/codestrata/application/intelligence",
        monorepo / "engine/src/codestrata/intelligence",
        monorepo / "engine/src/codestrata/application/engineering_intelligence",
        monorepo / "engine/src/codestrata/reporting/engineering_intelligence",
    ]
    hits: list[str] = []
    scanned = 0
    for root in candidates:
        if not root.exists():
            continue
        paths = [root] if root.is_file() else list(root.rglob("*.py"))
        for path in paths:
            if not path.is_file():
                continue
            scanned += 1
            text = read_text(path)
            for needle in (
                "create_assess_ai_provider",
                "AssessAIProviderRegistry",
                "AiEnrichmentService",
                "get_assess_ai_provider_registry",
            ):
                if needle in text:
                    hits.append(f"{path.relative_to(monorepo)}:{needle}")

    # Also scan portfolio / EIR generation entrypoints by name.
    for rel in (
        "engine/src/codestrata/cli/intelligence.py",
        "engine/src/codestrata/cli/eir.py",
        "engine/src/codestrata/application/portfolio",
    ):
        path = monorepo / rel
        if path.is_file():
            scanned += 1
            text = read_text(path)
            for needle in ("create_assess_ai_provider", "AiEnrichmentService"):
                if needle in text:
                    hits.append(f"{rel}:{needle}")
        elif path.is_dir():
            for py in path.rglob("*.py"):
                scanned += 1
                text = read_text(py)
                for needle in ("create_assess_ai_provider", "AiEnrichmentService"):
                    if needle in text:
                        hits.append(f"{py.relative_to(monorepo)}:{needle}")

    ok = not hits
    checks.append(
        check(
            "eir_boundary:no_provider_invoke",
            ok,
            f"scanned={scanned} hits={len(hits)}",
            "eir_boundary",
        )
    )
    checks.append(
        check(
            "eir_boundary:deferred_soft",
            True,
            "eir_provider_enrichment_deferred",
            "eir_boundary",
        )
    )

    summary = {
        "eir_invokes_providers": bool(hits),
        "hits": hits[:10],
        "deferred": True,
        "scanned": scanned,
    }
    return checks, defects, summary, limitations
