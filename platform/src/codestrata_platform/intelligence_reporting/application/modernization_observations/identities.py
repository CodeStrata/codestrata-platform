"""Deterministic modernization action identity and category catalog."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.intelligence_reporting.domain.enums import (
    ModernizationObservationCategory,
    PatternType,
)

ACTION_IDENTITY_CATALOG_VERSION = "modernization-action-identity-v1"

# Recommendation category → observation category (explicit, not title-derived).
_CATEGORY_TO_OBSERVATION: dict[str, ModernizationObservationCategory] = {
    "security": ModernizationObservationCategory.SECURITY_REMEDIATION,
    "dependency": ModernizationObservationCategory.DEPENDENCY_GOVERNANCE,
    "architecture": ModernizationObservationCategory.ARCHITECTURE_MODERNIZATION,
    "technical_debt": ModernizationObservationCategory.MAINTAINABILITY,
    "maintainability": ModernizationObservationCategory.MAINTAINABILITY,
    "testing": ModernizationObservationCategory.TESTING_ENABLEMENT,
    "cloud": ModernizationObservationCategory.CLOUD_ENABLEMENT,
    "cloud_readiness": ModernizationObservationCategory.CLOUD_ENABLEMENT,
    "ai_readiness": ModernizationObservationCategory.AI_ENABLEMENT,
    "ai": ModernizationObservationCategory.AI_ENABLEMENT,
    "modernization": ModernizationObservationCategory.SHARED_FOUNDATION,
    "operations": ModernizationObservationCategory.OPERATIONAL_READINESS,
}

_HEAD_TO_OBSERVATION: dict[str, ModernizationObservationCategory] = {
    "security_intelligence": ModernizationObservationCategory.SECURITY_REMEDIATION,
    "dependency_intelligence": ModernizationObservationCategory.DEPENDENCY_GOVERNANCE,
    "architecture_intelligence": ModernizationObservationCategory.ARCHITECTURE_MODERNIZATION,
    "technical_debt_intelligence": ModernizationObservationCategory.MAINTAINABILITY,
    "cloud_readiness": ModernizationObservationCategory.CLOUD_ENABLEMENT,
    "ai_readiness": ModernizationObservationCategory.AI_ENABLEMENT,
    "modernization_assessment": ModernizationObservationCategory.SHARED_FOUNDATION,
}

_CATALOG_TITLES: dict[ModernizationObservationCategory, str] = {
    ModernizationObservationCategory.SECURITY_REMEDIATION: "Security remediation",
    ModernizationObservationCategory.DEPENDENCY_GOVERNANCE: "Dependency governance",
    ModernizationObservationCategory.ARCHITECTURE_MODERNIZATION: "Architecture modernization",
    ModernizationObservationCategory.MAINTAINABILITY: "Complexity reduction",
    ModernizationObservationCategory.TESTING_ENABLEMENT: "Testing enablement",
    ModernizationObservationCategory.CLOUD_ENABLEMENT: "Cloud enablement",
    ModernizationObservationCategory.AI_ENABLEMENT: "AI enablement",
    ModernizationObservationCategory.SHARED_FOUNDATION: "Shared foundation",
    ModernizationObservationCategory.OPERATIONAL_READINESS: "Operational readiness",
    ModernizationObservationCategory.OTHER: "Other modernization actions",
}

# Reviewed pattern → action mappings (conservative).
# source_rule_ids empty means recommendation-pattern category match.
_PATTERN_SUPPORT_MAP: tuple[dict[str, object], ...] = (
    {
        "mapping_id": "security-credential-literal",
        "source_pattern_type": PatternType.RECURRING_CONFIGURATION_CONDITION.value,
        "source_rule_ids": ("security.credential-literal",),
        "target_category": ModernizationObservationCategory.SECURITY_REMEDIATION.value,
        "required_support": "recommendation",
    },
    {
        "mapping_id": "security-rule-demo",
        "source_pattern_type": PatternType.RECURRING_RULE.value,
        "source_rule_ids": ("rule.demo",),
        "target_category": ModernizationObservationCategory.SECURITY_REMEDIATION.value,
        "required_support": "recommendation",
    },
    {
        "mapping_id": "dependency-mutable-version",
        "source_pattern_type": PatternType.RECURRING_DEPENDENCY_CONDITION.value,
        "source_rule_ids": ("dependency.mutable-version",),
        "target_category": ModernizationObservationCategory.DEPENDENCY_GOVERNANCE.value,
        "required_support": "recommendation",
    },
)


@dataclass(frozen=True, slots=True)
class ModernizationActionIdentity:
    provider_key: str
    category_key: str
    assessment_head_id: str
    observation_category: ModernizationObservationCategory
    limitations: tuple[str, ...] = ()

    @property
    def action_identity(self) -> str:
        return (
            f"modernization-action:{self.provider_key}:"
            f"{self.category_key}:{self.assessment_head_id}"
        )

    @property
    def normalized_subject(self) -> str:
        return self.action_identity


def resolve_observation_category(
    *,
    recommendation_category: str,
    assessment_head_id: str,
) -> ModernizationObservationCategory | None:
    cat = recommendation_category.strip().lower().replace(" ", "_").replace("-", "_")
    if cat in _CATEGORY_TO_OBSERVATION:
        return _CATEGORY_TO_OBSERVATION[cat]
    if assessment_head_id in _HEAD_TO_OBSERVATION:
        return _HEAD_TO_OBSERVATION[assessment_head_id]
    return None


def build_action_identity(
    *,
    provider_id: str | None,
    recommendation_category: str,
    assessment_head_id: str,
) -> ModernizationActionIdentity | None:
    observation_category = resolve_observation_category(
        recommendation_category=recommendation_category,
        assessment_head_id=assessment_head_id,
    )
    if observation_category is None:
        return None
    cat = recommendation_category.strip().lower().replace(" ", "_").replace("-", "_") or "none"
    provider = (provider_id or "").strip() or "none"
    limitations: tuple[str, ...] = ()
    if provider == "none":
        limitations = ("action_identity_uses_category_without_provider",)
    return ModernizationActionIdentity(
        provider_key=provider,
        category_key=cat,
        assessment_head_id=assessment_head_id,
        observation_category=observation_category,
        limitations=limitations,
    )


def catalog_title(category: ModernizationObservationCategory) -> str:
    return _CATALOG_TITLES.get(category, "Other modernization actions")


def pattern_support_mappings() -> tuple[dict[str, object], ...]:
    return _PATTERN_SUPPORT_MAP
