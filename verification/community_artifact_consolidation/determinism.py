"""Deterministic JSON helpers for Slice 17.12."""

from __future__ import annotations

import json
import re
from typing import Any

_FORBIDDEN = re.compile(
    r"(password\s*=|Bearer\s+[A-Za-z0-9._-]+|/Users/[^\s\"']+|arn:aws:[^\s\"']+|\b\d{12}\b)",
    re.I,
)


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def report_text_is_safe(text: str) -> bool:
    return _FORBIDDEN.search(text) is None
