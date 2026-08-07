"""Bounded router result models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RouterResult:
    target: str
    status: str
    dry_run: bool
    target_policy_version: str
    target_manifest_schema: str
    visibility: str
    destination_semantics: str
    managed_file_count: int = 0
    additions: int = 0
    modifications: int = 0
    removals: int = 0
    conflicts: int = 0
    limitation_codes: list[str] = field(default_factory=list)
    error_category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "additions": self.additions,
            "conflicts": self.conflicts,
            "destination_semantics": self.destination_semantics,
            "dry_run": self.dry_run,
            "error_category": self.error_category,
            "limitation_codes": sorted(self.limitation_codes),
            "managed_file_count": self.managed_file_count,
            "modifications": self.modifications,
            "removals": self.removals,
            "status": self.status,
            "target": self.target,
            "target_manifest_schema": self.target_manifest_schema,
            "target_policy_version": self.target_policy_version,
            "visibility": self.visibility,
        }
        return {k: v for k, v in payload.items() if v is not None}


def dumps_result(result: RouterResult) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n"
