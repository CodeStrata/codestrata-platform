"""Reviewed extension operation catalog (Slice 7.10).

Maps public VS Code / Cursor extension commands to canonical operations.
Raw command IDs are never required by the server contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EXTENSION_OPERATION_CATALOG_ID = "extension-operation-catalog"
EXTENSION_OPERATION_CATALOG_VERSION = "1.0"
EXTENSION_OPERATION_CATALOG_URN = (
    f"{EXTENSION_OPERATION_CATALOG_ID}:{EXTENSION_OPERATION_CATALOG_VERSION}"
)

# Canonical operations derived from vscode-plugin + cursor-plugin public commands.
CANONICAL_EXTENSION_OPERATIONS: tuple[str, ...] = (
    "activate",
    "ask_suggested",
    "assess",
    "assess_with_ai",
    "check_environment",
    "clear_results",
    "copy_conversation_prompt",
    "filter_findings",
    "init_config",
    "install_engine",
    "missing_assessment_help",
    "open_documentation",
    "open_output",
    "open_report",
    "refresh_findings",
    "refresh_recommendations",
    "set_findings_group_by",
    "show_findings",
    "show_recommendations",
    "show_welcome",
)

# Alias → canonical. Clients may submit either; payload stores canonical only.
# Includes reviewed VS Code command IDs and product-specific aliases.
EXTENSION_OPERATION_ALIASES: dict[str, str] = {
    "codestrata.assess": "assess",
    "codestrata.assessWithAi": "assess_with_ai",
    "codestrata.askSuggested": "ask_suggested",
    "codestrata.checkEnvironment": "check_environment",
    "codestrata.clearAssessment": "clear_results",
    "codestrata.clearResults": "clear_results",
    "codestrata.copyConversationPrompt": "copy_conversation_prompt",
    "codestrata.doctor": "check_environment",
    "codestrata.filterFindings": "filter_findings",
    "codestrata.init": "init_config",
    "codestrata.installEngine": "install_engine",
    "codestrata.missingAssessmentHelp": "missing_assessment_help",
    "codestrata.openDocumentation": "open_documentation",
    "codestrata.openHtmlReport": "open_report",
    "codestrata.openOutput": "open_output",
    "codestrata.refreshAssessment": "refresh_findings",
    "codestrata.refreshFindings": "refresh_findings",
    "codestrata.refreshRecommendations": "refresh_recommendations",
    "codestrata.setFindingsGroupBy": "set_findings_group_by",
    "codestrata.showFindings": "show_findings",
    "codestrata.showRecommendations": "show_recommendations",
    "codestrata.showWelcome": "show_welcome",
}


@dataclass(frozen=True, slots=True)
class ExtensionOperationCatalog:
    """Deterministic operation catalog — version bump required for semantic changes."""

    catalog_id: str = EXTENSION_OPERATION_CATALOG_ID
    catalog_version: str = EXTENSION_OPERATION_CATALOG_VERSION
    canonical_operations: tuple[str, ...] = CANONICAL_EXTENSION_OPERATIONS
    aliases: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if self.catalog_id != EXTENSION_OPERATION_CATALOG_ID:
            raise ValueError("unsupported extension operation catalog id")
        if self.catalog_version != EXTENSION_OPERATION_CATALOG_VERSION:
            raise ValueError("unsupported extension operation catalog version")
        ops = tuple(sorted(set(self.canonical_operations)))
        if not ops:
            raise ValueError("canonical operations required")
        alias_map = dict(self.aliases or EXTENSION_OPERATION_ALIASES)
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
    def default(cls) -> ExtensionOperationCatalog:
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


def default_operation_catalog() -> ExtensionOperationCatalog:
    return ExtensionOperationCatalog.default()
