"""Deterministic pattern title and statement templates."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.recurring_patterns.candidates import (
    PatternCandidate,
)
from codestrata_platform.intelligence_reporting.domain.enums import PatternType

STATEMENT_TEMPLATE_VERSION = "recurring-pattern-statement-v1"

_FORBIDDEN_WORDS = (
    "systemic",
    "widespread",
    "dominant",
    "critical portfolio",
    "industry",
    "maturity",
    "should standardize",
    "must migrate",
    "improving",
    "declining",
    "recommend that",
)


def render_title(candidate: PatternCandidate) -> str:
    subject = candidate.subject.normalized_identity
    if candidate.pattern_type is PatternType.RECURRING_RECOMMENDATION:
        return f"Recurring recommendation intent ({subject})"
    if candidate.pattern_type is PatternType.RECURRING_TECHNOLOGY_CONDITION:
        return f"Recurring technology conflict ({subject})"
    rule = candidate.subject.rule_ids[0] if candidate.subject.rule_ids else subject
    return f"Recurring condition: {rule}"


def render_statement(
    candidate: PatternCandidate,
    *,
    repository_count: int,
    denominator_count: int,
    head_label: str,
) -> str:
    """Bounded factual statement. Includes numerator/denominator."""

    if candidate.pattern_type is PatternType.RECURRING_RECOMMENDATION:
        text = (
            f"Equivalent deterministic recommendation intent was produced in "
            f"{repository_count} of {denominator_count} repositories with comparable "
            f"{head_label} assessment."
        )
    elif candidate.pattern_type is PatternType.RECURRING_TECHNOLOGY_CONDITION:
        text = (
            f"Conflicting technology version declarations for the same technology were "
            f"identified in {repository_count} of {denominator_count} repositories with "
            f"eligible Technology Inventory."
        )
    elif candidate.subject.rule_ids:
        rule = candidate.subject.rule_ids[0]
        text = (
            f"`{rule}` was reported in {repository_count} of {denominator_count} "
            f"repositories where {head_label} assessment was comparable."
        )
    else:
        text = (
            f"A recurring deterministic condition was reported in "
            f"{repository_count} of {denominator_count} repositories where "
            f"{head_label} assessment was comparable."
        )
    lowered = text.lower()
    for token in _FORBIDDEN_WORDS:
        if token in lowered:
            raise ValueError(f"unsafe pattern statement wording: {token}")
    return text


def head_display_label(assessment_head_ids: tuple[str, ...]) -> str:
    if not assessment_head_ids:
        return "assessment-head"
    head = assessment_head_ids[0]
    return head.replace("_", " ")
