"""Provider family taxonomy."""

from __future__ import annotations

from verification.community_insights_ingestion.contract import PROVIDER_FAMILIES


def closed_providers() -> tuple[str, ...]:
    return PROVIDER_FAMILIES
