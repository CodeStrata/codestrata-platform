"""Deterministic JSON helpers."""

from __future__ import annotations

import json
from typing import Any


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
