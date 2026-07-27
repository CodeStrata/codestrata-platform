"""Executive Intelligence feature-gating policies."""

from __future__ import annotations

import os

EXECUTIVE_INTELLIGENCE_ENABLED_ENV = "CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED"


def executive_intelligence_enabled() -> bool:
    raw = os.environ.get(EXECUTIVE_INTELLIGENCE_ENABLED_ENV, "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


__all__ = ["EXECUTIVE_INTELLIGENCE_ENABLED_ENV", "executive_intelligence_enabled"]
