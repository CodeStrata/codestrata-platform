"""Deterministic modernization observation titles and statements."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.modernization_observations.identities import (
    catalog_title,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ModernizationObservationCategory,
)

STATEMENT_TEMPLATE_VERSION = "modernization-observation-statement-v1"

_FORBIDDEN = (
    "must ",
    "should ",
    "portfolio should",
    "urgent",
    "roi",
    "staffing",
    "cost",
    "timeline",
    "migration plan",
    "industry",
    "improving",
    "declining",
    "standardize all",
)


def render_title(category: ModernizationObservationCategory) -> str:
    return catalog_title(category)


def render_statement(
    *,
    category: ModernizationObservationCategory,
    repository_count: int,
    denominator_count: int,
    head_label: str,
) -> str:
    label = catalog_title(category).lower()
    text = (
        f"{label[0].upper()}{label[1:]} actions were produced for "
        f"{repository_count} of {denominator_count} repositories with comparable "
        f"{head_label} assessment."
    )
    lowered = text.lower()
    for token in _FORBIDDEN:
        if token in lowered:
            raise ValueError(f"unsafe observation statement wording: {token}")
    return text


def head_display_label(assessment_head_ids: tuple[str, ...]) -> str:
    if not assessment_head_ids:
        return "assessment-head"
    return assessment_head_ids[0].replace("_", " ")
