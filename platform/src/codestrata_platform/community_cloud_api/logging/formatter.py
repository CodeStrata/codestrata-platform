"""Deterministic JSON log formatting."""

from __future__ import annotations

import json
from typing import Any, Mapping

from codestrata_platform.community_cloud_api.logging.models import StructuredLogEvent
from codestrata_platform.community_cloud_api.logging.sanitization import (
    ensure_no_payload_fields,
)


def format_log_event(event: StructuredLogEvent) -> str:
    """Serialize a structured event as compact sorted-key JSON + newline."""

    payload = ensure_no_payload_fields(event.to_stable_dict())
    return dumps_log_json(payload) + "\n"


def dumps_log_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        dict(sorted(payload.items(), key=lambda item: str(item[0]))),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
