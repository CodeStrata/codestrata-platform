"""Reviewed AI capability / provider / model catalogs (Slice 7.11)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

AI_CAPABILITY_CATALOG_ID = "ai-capability-catalog"
AI_CAPABILITY_CATALOG_VERSION = "1.0"
AI_CAPABILITY_CATALOG_URN = (
    f"{AI_CAPABILITY_CATALOG_ID}:{AI_CAPABILITY_CATALOG_VERSION}"
)

AI_PROVIDER_FAMILY_CATALOG_ID = "ai-provider-family-catalog"
AI_PROVIDER_FAMILY_CATALOG_VERSION = "1.0"
AI_PROVIDER_FAMILY_CATALOG_URN = (
    f"{AI_PROVIDER_FAMILY_CATALOG_ID}:{AI_PROVIDER_FAMILY_CATALOG_VERSION}"
)

AI_MODEL_FAMILY_CATALOG_ID = "ai-model-family-catalog"
AI_MODEL_FAMILY_CATALOG_VERSION = "1.0"
AI_MODEL_FAMILY_CATALOG_URN = (
    f"{AI_MODEL_FAMILY_CATALOG_ID}:{AI_MODEL_FAMILY_CATALOG_VERSION}"
)

# Community assess --with-ai is Modernization Advisor only.
CANONICAL_AI_CAPABILITIES: tuple[str, ...] = ("modernization_advisor",)

AI_CAPABILITY_ALIASES: dict[str, str] = {
    "modernization-advisor": "modernization_advisor",
    "ai_enrichment": "modernization_advisor",
    "assess_with_ai": "modernization_advisor",
}

# Only providers with real Engine integrations.
CANONICAL_AI_PROVIDER_FAMILIES: tuple[str, ...] = (
    "aws_bedrock",
    "openai",
    "openrouter",
    "unavailable",
)

AI_PROVIDER_FAMILY_ALIASES: dict[str, str] = {
    "bedrock": "aws_bedrock",
    "amazon_bedrock": "aws_bedrock",
}

# Broad families — raw model IDs rejected.
CANONICAL_AI_MODEL_FAMILIES: tuple[str, ...] = (
    "amazon_nova_family",
    "gpt_family",
    "other_supported",
    "unavailable",
)

AI_MODEL_FAMILY_ALIASES: dict[str, str] = {
    "nova": "amazon_nova_family",
    "gpt": "gpt_family",
    "openai_gpt": "gpt_family",
}


@dataclass(frozen=True, slots=True)
class _CatalogBase:
    catalog_id: str
    catalog_version: str
    canonical_values: tuple[str, ...]
    aliases: dict[str, str]

    @property
    def catalog_token(self) -> str:
        return f"{self.catalog_id}:{self.catalog_version}"

    def canonicalize(self, value: str) -> str | None:
        text = (value or "").strip()
        if text in self.canonical_values:
            return text
        if text in self.aliases:
            return self.aliases[text]
        return None

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "aliases": dict(self.aliases),
            "canonical_values": list(self.canonical_values),
            "catalog_id": self.catalog_id,
            "catalog_token": self.catalog_token,
            "catalog_version": self.catalog_version,
        }


def _build_catalog(
    *,
    catalog_id: str,
    catalog_version: str,
    canonical: tuple[str, ...],
    aliases: dict[str, str],
) -> _CatalogBase:
    ops = tuple(sorted(set(canonical)))
    if not ops:
        raise ValueError("canonical values required")
    alias_map = dict(aliases)
    for alias, target in alias_map.items():
        if not alias or any(ch.isspace() for ch in alias):
            raise ValueError("invalid catalog alias")
        if target not in ops:
            raise ValueError(f"alias target not in catalog: {target}")
    return _CatalogBase(
        catalog_id=catalog_id,
        catalog_version=catalog_version,
        canonical_values=ops,
        aliases={key: alias_map[key] for key in sorted(alias_map)},
    )


@dataclass(frozen=True, slots=True)
class AiCapabilityCatalog:
    catalog_id: str = AI_CAPABILITY_CATALOG_ID
    catalog_version: str = AI_CAPABILITY_CATALOG_VERSION
    canonical_capabilities: tuple[str, ...] = CANONICAL_AI_CAPABILITIES
    aliases: dict[str, str] | None = None

    def __post_init__(self) -> None:
        built = _build_catalog(
            catalog_id=self.catalog_id,
            catalog_version=self.catalog_version,
            canonical=self.canonical_capabilities,
            aliases=dict(self.aliases or AI_CAPABILITY_ALIASES),
        )
        if built.catalog_id != AI_CAPABILITY_CATALOG_ID:
            raise ValueError("unsupported ai capability catalog id")
        if built.catalog_version != AI_CAPABILITY_CATALOG_VERSION:
            raise ValueError("unsupported ai capability catalog version")
        object.__setattr__(self, "canonical_capabilities", built.canonical_values)
        object.__setattr__(self, "aliases", built.aliases)

    @property
    def catalog_token(self) -> str:
        return f"{self.catalog_id}:{self.catalog_version}"

    @classmethod
    def default(cls) -> AiCapabilityCatalog:
        return cls()

    def canonicalize(self, value: str) -> str | None:
        text = (value or "").strip()
        if text in self.canonical_capabilities:
            return text
        aliases = self.aliases or {}
        if text in aliases:
            return aliases[text]
        return None

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "aliases": dict(self.aliases or {}),
            "canonical_capabilities": list(self.canonical_capabilities),
            "catalog_id": self.catalog_id,
            "catalog_token": self.catalog_token,
            "catalog_version": self.catalog_version,
        }


@dataclass(frozen=True, slots=True)
class AiProviderFamilyCatalog:
    catalog_id: str = AI_PROVIDER_FAMILY_CATALOG_ID
    catalog_version: str = AI_PROVIDER_FAMILY_CATALOG_VERSION
    canonical_families: tuple[str, ...] = CANONICAL_AI_PROVIDER_FAMILIES
    aliases: dict[str, str] | None = None

    def __post_init__(self) -> None:
        built = _build_catalog(
            catalog_id=self.catalog_id,
            catalog_version=self.catalog_version,
            canonical=self.canonical_families,
            aliases=dict(self.aliases or AI_PROVIDER_FAMILY_ALIASES),
        )
        if built.catalog_id != AI_PROVIDER_FAMILY_CATALOG_ID:
            raise ValueError("unsupported ai provider family catalog id")
        if built.catalog_version != AI_PROVIDER_FAMILY_CATALOG_VERSION:
            raise ValueError("unsupported ai provider family catalog version")
        object.__setattr__(self, "canonical_families", built.canonical_values)
        object.__setattr__(self, "aliases", built.aliases)

    @property
    def catalog_token(self) -> str:
        return f"{self.catalog_id}:{self.catalog_version}"

    @classmethod
    def default(cls) -> AiProviderFamilyCatalog:
        return cls()

    def canonicalize(self, value: str) -> str | None:
        text = (value or "").strip()
        if text in self.canonical_families:
            return text
        aliases = self.aliases or {}
        if text in aliases:
            return aliases[text]
        return None

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "aliases": dict(self.aliases or {}),
            "canonical_families": list(self.canonical_families),
            "catalog_id": self.catalog_id,
            "catalog_token": self.catalog_token,
            "catalog_version": self.catalog_version,
        }


@dataclass(frozen=True, slots=True)
class AiModelFamilyCatalog:
    catalog_id: str = AI_MODEL_FAMILY_CATALOG_ID
    catalog_version: str = AI_MODEL_FAMILY_CATALOG_VERSION
    canonical_families: tuple[str, ...] = CANONICAL_AI_MODEL_FAMILIES
    aliases: dict[str, str] | None = None

    def __post_init__(self) -> None:
        built = _build_catalog(
            catalog_id=self.catalog_id,
            catalog_version=self.catalog_version,
            canonical=self.canonical_families,
            aliases=dict(self.aliases or AI_MODEL_FAMILY_ALIASES),
        )
        if built.catalog_id != AI_MODEL_FAMILY_CATALOG_ID:
            raise ValueError("unsupported ai model family catalog id")
        if built.catalog_version != AI_MODEL_FAMILY_CATALOG_VERSION:
            raise ValueError("unsupported ai model family catalog version")
        object.__setattr__(self, "canonical_families", built.canonical_values)
        object.__setattr__(self, "aliases", built.aliases)

    @property
    def catalog_token(self) -> str:
        return f"{self.catalog_id}:{self.catalog_version}"

    @classmethod
    def default(cls) -> AiModelFamilyCatalog:
        return cls()

    def canonicalize(self, value: str) -> str | None:
        text = (value or "").strip()
        if text in self.canonical_families:
            return text
        aliases = self.aliases or {}
        if text in aliases:
            return aliases[text]
        return None

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "aliases": dict(self.aliases or {}),
            "canonical_families": list(self.canonical_families),
            "catalog_id": self.catalog_id,
            "catalog_token": self.catalog_token,
            "catalog_version": self.catalog_version,
        }


def default_capability_catalog() -> AiCapabilityCatalog:
    return AiCapabilityCatalog.default()


def default_provider_catalog() -> AiProviderFamilyCatalog:
    return AiProviderFamilyCatalog.default()


def default_model_catalog() -> AiModelFamilyCatalog:
    return AiModelFamilyCatalog.default()
