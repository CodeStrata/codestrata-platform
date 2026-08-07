"""Exporter data models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

Classification = Literal[
    "export_required",
    "export_optional",
    "generated_root_file",
    "generated_artifact",
    "generated_not_exported",
    "transformed_export",
]

ModeCategory = Literal["regular", "executable"]


@dataclass(frozen=True, slots=True)
class PlannedFile:
    """One destination file in the desired export."""

    destination_path: str
    content: bytes
    mode: int
    classification: Classification
    source_relative: str | None = None

    @property
    def mode_category(self) -> ModeCategory:
        return "executable" if (self.mode & 0o111) else "regular"

    @property
    def sha256(self) -> str:
        import hashlib

        return hashlib.sha256(self.content).hexdigest()

    @property
    def size(self) -> int:
        return len(self.content)


@dataclass
class ChangePlan:
    additions: list[str] = field(default_factory=list)
    modifications: list[str] = field(default_factory=list)
    removals: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    unmanaged: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "additions": sorted(self.additions),
            "conflicts": sorted(self.conflicts),
            "modifications": sorted(self.modifications),
            "removals": sorted(self.removals),
            "unchanged": sorted(self.unchanged),
            "unmanaged": sorted(self.unmanaged),
        }


@dataclass
class ExportDiagnostics:
    target: str
    status: str
    dry_run: bool
    source_policy_version: str
    manifest_schema_version: str
    file_count: int
    generated_file_count: int
    executable_file_count: int
    excluded_category_count: int
    addition_count: int
    modification_count: int
    removal_count: int
    conflict_count: int
    limitation_codes: list[str] = field(default_factory=list)
    error_category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "addition_count": self.addition_count,
            "conflict_count": self.conflict_count,
            "dry_run": self.dry_run,
            "error_category": self.error_category,
            "excluded_category_count": self.excluded_category_count,
            "executable_file_count": self.executable_file_count,
            "file_count": self.file_count,
            "generated_file_count": self.generated_file_count,
            "limitation_codes": sorted(self.limitation_codes),
            "manifest_schema_version": self.manifest_schema_version,
            "modification_count": self.modification_count,
            "removal_count": self.removal_count,
            "source_policy_version": self.source_policy_version,
            "status": self.status,
            "target": self.target,
        }
        return {k: v for k, v in payload.items() if v is not None}


def dumps_canonical(data: dict[str, Any]) -> bytes:
    """UTF-8 JSON with sorted keys, 2-space indent, trailing newline."""

    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")
