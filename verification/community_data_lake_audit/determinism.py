"""Determinism helpers for Slice 15.1."""

from __future__ import annotations

import json
from typing import Any


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def reports_byte_identical(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return dict_to_canonical_json(a) == dict_to_canonical_json(b)


def report_text_is_safe(text: str) -> tuple[bool, str]:
    if "/Users/" in text or "/home/" in text or "file://" in text:
        return False, "path_leak"
    if "timestamp" in text.lower():
        return False, "timestamp"
    return True, "safe"
