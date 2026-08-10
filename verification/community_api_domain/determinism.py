"""Determinism helpers for Slice 17.14."""

from __future__ import annotations

import json
import re
from typing import Any

_EXECUTE_API_HOST = re.compile(r"execute-api\.[a-z0-9-]+\.amazonaws\.com", re.I)


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
    if "akia" in lowered or "-----begin" in lowered or "aws_secret_access_key" in lowered:
        return False, "secret_leak"
    if "arn:aws:" in lowered:
        return False, "arn_leak"
    if re.search(r"\b\d{12}\b", text):
        return False, "account_id"
    if "ghp_" in text or "github_pat_" in text:
        return False, "github_token"
    if "s3://" in lowered:
        return False, "object_uri_leak"
    if _EXECUTE_API_HOST.search(text):
        return False, "execute_api_public_authority"
    if re.search(r"raw/stream=[^/]+/schema_version=[^/]+/year=\d{4}", lowered):
        return False, "object_key_leak"
    if re.search(r"\b[a-z0-9]{10}\.execute-api\.", lowered):
        return False, "api_gateway_id_leak"
    return True, "safe"
