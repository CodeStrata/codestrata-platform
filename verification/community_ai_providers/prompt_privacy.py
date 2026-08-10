"""Prompt privacy: document exact fields sent; forbid false 'no findings' claims."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import (
    CONTEXT_PY,
    DOCS_AI_PROVIDERS,
    PROMPT_PY,
)
from verification.community_ai_providers.helpers import check, hard_defect, read_text
from verification.community_ai_providers.models import CheckResult, Defect

# Exact compact fields from AiEnrichmentContext / FindingSummaryItem (source).
SENT_FIELDS = (
    "repository identity (repository_key, display_name, source_type, file_count)",
    "finding summaries (id, rule_id, title, severity, category, summary, evidence_refs)",
    "recommendation summaries (id, title, priority, category, summary, related_finding_ids, action_titles)",
    "technology summaries",
    "dependency summaries (bounded)",
    "allowed_finding_ids / allowed_recommendation_ids",
)

NOT_SENT = (
    "full source file dumps",
    "raw repository trees as complete source",
)


def check_prompt_privacy(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    context = read_text(monorepo / CONTEXT_PY)
    prompt = read_text(monorepo / PROMPT_PY)
    docs = read_text(monorepo / DOCS_AI_PROVIDERS) if (monorepo / DOCS_AI_PROVIDERS).is_file() else ""

    compact = (
        "FindingSummaryItem" in context
        and "DEFAULT_MAX_SUMMARY_CHARS" in context
        and "Compact enrichment context JSON" in prompt
    )
    checks.append(
        check(
            "prompt_privacy:compact_summaries",
            compact,
            "compact findings/recs summaries via AiEnrichmentContext",
            "prompt_privacy",
        )
    )
    if not compact:
        defects.append(
            hard_defect(
                "prompt_not_compact",
                "prompt_privacy:compact_summaries",
                "compact",
                "missing",
            )
        )

    # Docs must not falsely claim "no findings sent".
    false_claim = (
        "no findings sent" in docs.lower()
        or "does not send findings" in docs.lower()
        or "never sends findings" in docs.lower()
    )
    checks.append(
        check(
            "prompt_privacy:docs_no_false_no_findings",
            not false_claim,
            "docs must not claim 'no findings sent'",
            "prompt_privacy",
        )
    )
    if false_claim:
        defects.append(
            hard_defect(
                "docs_false_privacy_claim",
                "prompt_privacy:docs_no_false_no_findings",
                "accurate",
                "false no-findings claim",
            )
        )

    summary = {
        "sent_fields": list(SENT_FIELDS),
        "not_sent": list(NOT_SENT),
        "full_source_dumps": False,
        "findings_summaries_sent": True,
        "docs_false_no_findings_claim": false_claim,
    }
    return checks, defects, summary
