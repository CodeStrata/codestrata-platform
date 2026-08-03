"""Section helpers — rendering is centralized in renderer.py for parity."""

from __future__ import annotations

SECTION_ORDER: tuple[str, ...] = (
    "cover",
    "scope",
    "orientation",
    "summary",
    "technology",
    "capability",
    "heads",
    "patterns",
    "observations",
    "confidence",
    "limitations",
    "drilldowns",
    "methodology",
    "metadata",
)
