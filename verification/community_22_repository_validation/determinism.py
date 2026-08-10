"""Deterministic JSON helpers for Slice 17.13."""

from __future__ import annotations

import json
import re
from typing import Any

_FORBIDDEN = re.compile(
    r"(password\s*=|Bearer\s+[A-Za-z0-9._-]+|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+"
    r"|/Users/[^\s\"']+|/home/[^\s\"']+|arn:aws:[^\s\"']+|\b\d{12}\b|s3://[^\s\"']+)",
    re.I,
)


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def report_text_is_safe(text: str) -> bool:
    return _FORBIDDEN.search(text) is None


def reports_byte_identical(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return dict_to_canonical_json(left) == dict_to_canonical_json(right)
