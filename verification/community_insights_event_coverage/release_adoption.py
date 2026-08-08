"""Release adoption helpers."""

from __future__ import annotations

from typing import Any


def release_rules() -> dict[str, Any]:
    return {
        "streams": ["cli_event", "extension_event"],
        "fields": ["payload.client.name", "payload.client.version"],
        "no_new_user_identity": True,
    }
