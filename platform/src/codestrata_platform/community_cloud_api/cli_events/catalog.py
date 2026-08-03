"""Reviewed CLI operation catalog (Slice 7.9).

Maps public Community CLI commands/aliases to canonical operations.
Raw command text is never transmitted — only canonical operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CLI_OPERATION_CATALOG_ID = "cli-operation-catalog"
CLI_OPERATION_CATALOG_VERSION = "1.0"
CLI_OPERATION_CATALOG_URN = (
    f"{CLI_OPERATION_CATALOG_ID}:{CLI_OPERATION_CATALOG_VERSION}"
)

# Canonical operations derived from the public Community Typer CLI surface.
CANONICAL_CLI_OPERATIONS: tuple[str, ...] = (
    "about",
    "agent",
    "ai",
    "architecture",
    "assess",
    "config",
    "doctor",
    "evidence",
    "examples",
    "extensions",
    "help",
    "incremental",
    "init",
    "mcp",
    "onboard",
    "open",
    "report",
    "roadmap",
    "rules",
    "scan",
    "telemetry",
    "validate",
    "version",
    "welcome",
)

# Alias → canonical. Clients may submit either; payload stores canonical only.
CLI_OPERATION_ALIASES: dict[str, str] = {
    "report.open": "open",
    "report_open": "open",
    "report.validate": "validate",
    "report_validate": "validate",
    "--version": "version",
    "codestrata": "help",
}


@dataclass(frozen=True, slots=True)
class CliOperationCatalog:
    """Deterministic operation catalog — version bump required for semantic changes."""

    catalog_id: str = CLI_OPERATION_CATALOG_ID
    catalog_version: str = CLI_OPERATION_CATALOG_VERSION
    canonical_operations: tuple[str, ...] = CANONICAL_CLI_OPERATIONS
    aliases: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if self.catalog_id != CLI_OPERATION_CATALOG_ID:
            raise ValueError("unsupported cli operation catalog id")
        if self.catalog_version != CLI_OPERATION_CATALOG_VERSION:
            raise ValueError("unsupported cli operation catalog version")
        ops = tuple(sorted(set(self.canonical_operations)))
        if not ops:
            raise ValueError("canonical operations required")
        alias_map = dict(self.aliases or CLI_OPERATION_ALIASES)
        for alias, target in alias_map.items():
            if not alias or any(ch.isspace() for ch in alias):
                raise ValueError("invalid operation alias")
            if target not in ops:
                raise ValueError(f"alias target not in catalog: {target}")
        object.__setattr__(self, "canonical_operations", ops)
        object.__setattr__(
            self,
            "aliases",
            {key: alias_map[key] for key in sorted(alias_map)},
        )

    @property
    def catalog_token(self) -> str:
        return f"{self.catalog_id}:{self.catalog_version}"

    @classmethod
    def default(cls) -> CliOperationCatalog:
        return cls()

    def canonicalize(self, value: str) -> str | None:
        text = (value or "").strip()
        if text in self.canonical_operations:
            return text
        aliases = self.aliases or {}
        if text in aliases:
            return aliases[text]
        return None

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "aliases": dict(self.aliases or {}),
            "canonical_operations": list(self.canonical_operations),
            "catalog_id": self.catalog_id,
            "catalog_token": self.catalog_token,
            "catalog_version": self.catalog_version,
        }


def default_operation_catalog() -> CliOperationCatalog:
    return CliOperationCatalog.default()
