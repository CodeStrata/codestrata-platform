"""Language / ecosystem coverage helpers."""

from __future__ import annotations

from typing import Any


def language_rules() -> dict[str, Any]:
    return {
        "language_field": "payload.repository.primary_language",
        "ecosystem_field": "payload.repository.package_ecosystem",
        "allowed_ids": [
            "python",
            "java",
            "javascript",
            "typescript",
            "go",
            "csharp",
            "rust",
            "unknown",
            "unavailable",
        ],
        "named_ecosystems_present": True,
        "file_path_forbidden": True,
        "package_name_forbidden": True,
        "future_change": "CR-15.3-001",
    }
