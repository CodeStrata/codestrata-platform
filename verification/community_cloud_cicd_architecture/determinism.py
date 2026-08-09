"""Determinism helpers for Slice 17.1."""

from __future__ import annotations

import json
from typing import Any


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def reports_byte_identical(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return dict_to_canonical_json(a) == dict_to_canonical_json(b)


def report_text_is_safe(text: str) -> tuple[bool, str]:
    lowered = text.lower()
    if "/users/" in lowered or "/home/" in lowered:
        return False, "path_leak"
    if "file://" in lowered:
        return False, "file_uri"
    if '"timestamp"' in lowered:
        return False, "timestamp"
    if "akia" in lowered or "-----begin" in lowered:
        return False, "secret_leak"
    if "aws_secret_access_key" in lowered:
        return False, "aws_key"
    # Account IDs often 12 digits — avoid embedding real ones; placeholder text ok
    if "arn:aws:iam::" in lowered and any(ch.isdigit() for ch in lowered):
        # Allow architectural prose without concrete 12-digit account ids
        import re

        if re.search(r"arn:aws:iam::\d{12}:", text):
            return False, "account_id"
    return True, "safe"
