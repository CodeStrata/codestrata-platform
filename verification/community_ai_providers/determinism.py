"""Deterministic serialization helpers for Slice 17.20."""

from __future__ import annotations

import copy
import json
import re
from typing import Any

_VOLATILE_KEYS = frozenset(
    {
        "latency_ms",
        "duration_seconds",
        "bytes",
        "assessment_run_id",
        "generated_at_utc",
        "request_id",
        "current_path",
        "work_path",
    }
)
_COUNT_DETAIL = re.compile(r"count=|bytes=|ms=|path=", re.IGNORECASE)


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def strip_volatile_fields(payload: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(payload)
    for section_key, section in list(out.items()):
        if isinstance(section, dict):
            for vk in _VOLATILE_KEYS:
                if vk in section:
                    section[vk] = "<volatile>"
            for nested in section.values():
                if isinstance(nested, dict):
                    for vk in _VOLATILE_KEYS:
                        if vk in nested:
                            nested[vk] = "<volatile>"
                if isinstance(nested, list):
                    for row in nested:
                        if isinstance(row, dict):
                            for vk in _VOLATILE_KEYS:
                                if vk in row:
                                    row[vk] = "<volatile>"
        if section_key == "checks" and isinstance(section, list):
            for item in section:
                if not isinstance(item, dict):
                    continue
                detail = str(item.get("detail", ""))
                if _COUNT_DETAIL.search(detail):
                    item["detail"] = "<volatile>"
    return out


def canonical_for_determinism(payload: dict[str, Any]) -> str:
    return dict_to_canonical_json(strip_volatile_fields(payload))


__all__ = [
    "canonical_for_determinism",
    "dict_to_canonical_json",
    "strip_volatile_fields",
]
