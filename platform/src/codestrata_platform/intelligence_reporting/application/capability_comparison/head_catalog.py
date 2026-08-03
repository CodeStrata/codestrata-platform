"""Canonical assessment-head catalog for commercial capability comparison."""

from __future__ import annotations

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.normalization import (
    CANONICAL_ASSESSMENT_HEADS,
)

# Explicit aliases only — map informal names to canonical commercial head IDs.
_HEAD_ALIASES: dict[str, str] = {
    "security": "security_intelligence",
    "dependency": "dependency_intelligence",
    "architecture": "architecture_intelligence",
    "technical_debt": "technical_debt_intelligence",
    "tech_debt": "technical_debt_intelligence",
    "testing": "technical_debt_intelligence",
    "cloud": "cloud_readiness",
    "ai": "ai_readiness",
    "modernization": "modernization_assessment",
    "technology": "technology_inventory",
    "engineering": "engineering_intelligence",
}

COMMERCIAL_HEAD_CATALOG: tuple[str, ...] = CANONICAL_ASSESSMENT_HEADS


def canonicalize_assessment_head(head_id: str) -> str:
    """Return canonical commercial head ID. Unknown IDs raise unless caller catches."""

    raw = str(head_id).strip()
    if not raw:
        raise InvalidValueError(
            "assessment_head_id is required",
            reason_code="missing_assessment_head_id",
        )
    key = raw.lower().replace(" ", "_").replace("-", "_")
    if key in COMMERCIAL_HEAD_CATALOG:
        return key
    if key in _HEAD_ALIASES:
        return _HEAD_ALIASES[key]
    raise InvalidValueError(
        f"unknown assessment head: {head_id}",
        reason_code="unknown_assessment_head",
    )


def try_canonicalize_assessment_head(head_id: str) -> str | None:
    try:
        return canonicalize_assessment_head(head_id)
    except InvalidValueError:
        return None


def catalog_order_key(head_id: str) -> tuple[int, str]:
    try:
        idx = COMMERCIAL_HEAD_CATALOG.index(head_id)
    except ValueError:
        idx = len(COMMERCIAL_HEAD_CATALOG)
    return (idx, head_id)
