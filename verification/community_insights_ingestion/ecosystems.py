"""Package ecosystem taxonomy."""

from __future__ import annotations

from verification.community_insights_ingestion.contract import PACKAGE_ECOSYSTEMS


def closed_ecosystems() -> tuple[str, ...]:
    return PACKAGE_ECOSYSTEMS
