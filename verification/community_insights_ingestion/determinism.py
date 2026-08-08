"""Determinism helpers."""

from __future__ import annotations

import json
from typing import Any


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def reports_byte_identical(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return dict_to_canonical_json(a) == dict_to_canonical_json(b)


def report_text_is_safe(text: str) -> tuple[bool, str]:
    lowered = text.lower()
    for needle, reason in (
        ("/users/", "path_leak"),
        ("/home/", "path_leak"),
        ("file://", "path_leak"),
        ("timestamp", "timestamp"),
        ("@gmail", "pii"),
        ("sk-live", "secret"),
    ):
        if needle in lowered:
            return False, reason
    return True, "safe"
