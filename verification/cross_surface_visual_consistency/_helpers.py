"""Shared helpers for Slice 14.13 checks."""

from __future__ import annotations

from verification.cross_surface_visual_consistency.models import CheckResult, Defect


def add(
    checks: list[CheckResult],
    name: str,
    ok: bool,
    detail: str,
    category: str,
) -> None:
    checks.append(CheckResult(name=name, ok=ok, detail=detail, category=category))


def scan_forbidden(text: str, forbidden: tuple[str, ...]) -> list[str]:
    import re

    hits: list[str] = []
    for item in forbidden:
        if item == "Codestrata":
            if re.search(r"\bCodestrata\b", text):
                hits.append(item)
            continue
        lower = text.lower()
        if item.lower() in lower:
            hits.append(item)
    return hits


def scan_hex(text: str, hex_value: str) -> bool:
    return hex_value.lower() in text.lower()
