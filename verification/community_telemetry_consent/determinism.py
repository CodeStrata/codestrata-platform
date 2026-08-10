"""Deterministic serialization helpers."""

from __future__ import annotations

import json
from typing import Any

from verification.community_telemetry_consent.helpers import report_text_is_safe


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


__all__ = ["dict_to_canonical_json", "report_text_is_safe"]
