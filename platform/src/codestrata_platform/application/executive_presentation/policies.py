"""Executive Presentation feature-gating policies."""

from __future__ import annotations

import os

EXECUTIVE_PRESENTATION_ENABLED_ENV = "CODESTRATA_EXECUTIVE_PRESENTATION_ENABLED"


def executive_presentation_enabled() -> bool:
    raw = os.environ.get(EXECUTIVE_PRESENTATION_ENABLED_ENV, "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


__all__ = ["EXECUTIVE_PRESENTATION_ENABLED_ENV", "executive_presentation_enabled"]
