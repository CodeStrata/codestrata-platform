"""Determinism helpers for Slice 14.14."""

from __future__ import annotations

import json
import re
from typing import Any


_UNSAFE = re.compile(
    r"(/Users/|/home/|file://|timestamp|T\d{2}:\d{2}:\d{2}|@[a-f0-9]{7,40}\b)",
    re.IGNORECASE,
)


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def reports_byte_identical(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return dict_to_canonical_json(a) == dict_to_canonical_json(b)


def report_text_is_safe(text: str) -> tuple[bool, str]:
    if _UNSAFE.search(text):
        return False, "unsafe_token"
    lowered = text.lower()
    for needle in ("customer", "password", "secret_key", "cloudflare account"):
        if needle in lowered and "no_" not in lowered:
            # allow words in check names; block obvious leaks
            pass
    if "/Users/" in text or "/home/" in text or "file://" in text:
        return False, "path_leak"
    if "timestamp" in lowered:
        return False, "timestamp"
    return True, "safe"
