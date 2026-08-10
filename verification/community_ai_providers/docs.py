"""Docs checks for AI providers (OpenRouter + privacy wording)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import DOCS_AI_PROVIDERS
from verification.community_ai_providers.helpers import check, hard_defect, read_text
from verification.community_ai_providers.models import CheckResult, Defect


def check_docs(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    path = monorepo / DOCS_AI_PROVIDERS
    text = read_text(path) if path.is_file() else ""
    checks.append(
        check("docs:exists", path.is_file(), DOCS_AI_PROVIDERS, "docs")
    )
    if not path.is_file():
        defects.append(
            hard_defect("missing_docs", "docs:exists", "present", "absent")
        )
        return checks, defects, {"present": False}

    mentions = {
        "bedrock": "bedrock" in text.lower(),
        "openai": "openai" in text.lower(),
        "openrouter": "openrouter" in text.lower(),
    }
    for name, ok in mentions.items():
        checks.append(
            check(f"docs:mentions_{name}", ok, name, "docs")
        )
        if not ok:
            defects.append(
                hard_defect(
                    f"docs_missing_{name}",
                    f"docs:mentions_{name}",
                    "present",
                    "absent",
                )
            )

    openrouter_setup = "OPENROUTER_API_KEY" in text and (
        'provider = "openrouter"' in text
        or "provider = 'openrouter'" in text
        or "[ai.openrouter]" in text
    )
    checks.append(
        check(
            "docs:openrouter_setup",
            openrouter_setup,
            "OPENROUTER_API_KEY + [ai] provider=openrouter",
            "docs",
        )
    )
    if not openrouter_setup:
        defects.append(
            hard_defect(
                "docs_openrouter_setup",
                "docs:openrouter_setup",
                "present",
                "absent",
            )
        )

    no_ai_default = "--no-ai" in text and "default" in text.lower()
    checks.append(
        check("docs:no_ai_default", no_ai_default, "--no-ai default", "docs")
    )

    # Privacy: compact findings/recs — not "no findings sent"
    privacy_ok = (
        "compact" in text.lower()
        or "summar" in text.lower()
        or "findings" in text.lower()
    ) and ("no findings sent" not in text.lower())
    checks.append(
        check(
            "docs:privacy_wording",
            privacy_ok,
            "documents enrichment payload accurately",
            "docs",
        )
    )

    non_blocking = (
        "non-blocking" in text.lower()
        or "non blocking" in text.lower()
        or "exit code remains 0" in text.lower()
        or "enrichment skipped" in text.lower()
    )
    checks.append(
        check(
            "docs:provider_failure_non_blocking",
            non_blocking,
            "provider failure non-blocking documented",
            "docs",
        )
    )

    summary = {
        "path": DOCS_AI_PROVIDERS,
        "mentions": mentions,
        "openrouter_setup": openrouter_setup,
        "no_ai_default": no_ai_default,
        "privacy_ok": privacy_ok,
        "non_blocking": non_blocking,
    }
    return checks, defects, summary
