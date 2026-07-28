"""Strategic Portfolio Roadmap feature-gating policies."""

from __future__ import annotations

import os

STRATEGIC_ROADMAP_ENABLED_ENV = "CODESTRATA_STRATEGIC_ROADMAP_ENABLED"


def strategic_roadmap_enabled() -> bool:
    raw = os.environ.get(STRATEGIC_ROADMAP_ENABLED_ENV, "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


__all__ = ["STRATEGIC_ROADMAP_ENABLED_ENV", "strategic_roadmap_enabled"]
