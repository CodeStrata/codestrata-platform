"""Deterministic HTML anchors for website-safe EIR export."""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slug(value: str) -> str:
    text = _NON_ALNUM.sub("-", value.strip().lower()).strip("-")
    return text or "section"


def section_anchor(name: str) -> str:
    return f"section-{slug(name)}"


def drilldown_anchor(drilldown_id: str) -> str:
    return f"drilldown-{slug(drilldown_id.replace(':', '-'))}"


def pattern_anchor(pattern_id: str) -> str:
    return f"pattern-{slug(pattern_id.replace(':', '-'))}"


def observation_anchor(observation_id: str) -> str:
    return f"observation-{slug(observation_id.replace(':', '-'))}"
