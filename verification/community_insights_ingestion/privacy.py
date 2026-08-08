"""Privacy fixtures."""

from __future__ import annotations

from verification.community_insights_ingestion.contract import PRIVACY_FIXTURES


def adversarial_fixtures() -> tuple[str, ...]:
    return PRIVACY_FIXTURES
