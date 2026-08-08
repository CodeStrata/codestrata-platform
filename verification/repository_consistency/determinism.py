"""Determinism helpers for Slice 16.8."""

from __future__ import annotations

import json
from typing import Any


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def reports_byte_identical(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return dict_to_canonical_json(a) == dict_to_canonical_json(b)


def report_text_is_safe(text: str) -> tuple[bool, str]:
    lowered = text.lower()
    if "/users/" in lowered or "/home/" in lowered or "file://" in lowered:
        return False, "path_leak"
    if '"timestamp"' in lowered or "'timestamp'" in lowered:
        return False, "timestamp"
    if "-----begin" in lowered:
        return False, "secret_block"
    return True, "safe"
