"""Extract payload client type for authentication matching."""

from __future__ import annotations

from typing import Any


def extract_payload_client_type(model: Any) -> str | None:
    """Return payload client.name when present — never credentials."""

    if model is None:
        return None
    client = getattr(model, "client", None)
    if client is None:
        return None
    name = getattr(client, "name", None)
    if name is None:
        return None
    text = str(name).strip()
    return text or None
