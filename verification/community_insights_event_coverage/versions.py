"""CLI / release version helpers."""

from __future__ import annotations

from typing import Any


def version_rules() -> dict[str, Any]:
    return {
        "cli_version_field": "payload.client.version",
        "executable_path_forbidden": True,
        "release_dimensions": ["payload.client.name", "payload.client.version"],
        "no_new_release_identity": True,
    }
