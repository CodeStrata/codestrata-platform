"""Determinism helpers for Slice 17.11."""

from __future__ import annotations

import json
import re
from typing import Any

FORBIDDEN_REPORT_SUBSTRINGS = (
    "/users/",
    "/home/",
    "file://",
    '"timestamp"',
    "arn:aws:",
    "ghp_",
    "github_pat_",
    "aws_secret_access_key",
    "-----begin",
    "akia",
    "s3://",
    "session_secret",
    "cookie_value",
    '"verifier"',
    '"salt"',
    '"derived_key"',
    "scrypt:",
)


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def reports_byte_identical(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return dict_to_canonical_json(a) == dict_to_canonical_json(b)


def report_text_is_safe(text: str) -> tuple[bool, str]:
    lowered = text.lower()
    for needle in FORBIDDEN_REPORT_SUBSTRINGS:
        if needle.lower() in lowered:
            return False, f"forbidden:{needle}"
    if re.search(r"\b\d{12}\b", text):
        return False, "account_id"
    if re.search(r"raw/stream=[^/]+/schema_version=[^/]+/year=\d{4}", lowered):
        return False, "object_key_leak"
    return True, "safe"
