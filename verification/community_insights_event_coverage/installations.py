"""Installation metric semantics."""

from __future__ import annotations

from typing import Any


def total_installations_rules() -> dict[str, Any]:
    return {
        "metric": "total_anonymous_installations",
        "must_not_use": "raw_event_count",
        "dedup": "payload.installation_id",
        "stable_when_present": True,
    }
