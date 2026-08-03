"""RepositoryDrilldownPolicy and result models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)


class LegacyDrilldownPolicy(StrEnum):
    EXCLUDE = "exclude"
    LIMITED = "limited"
    REJECT = "reject"


class AnonymizationPolicy(StrEnum):
    USE_STABLE_ALIAS = "use_stable_alias"
    USE_PROVIDED_WHEN_SAFE = "use_provided_when_safe"


class EntitySelectionPolicy(StrEnum):
    SEVERITY_THEN_CONFIDENCE = "severity_then_confidence"
    PRIORITY_THEN_CONFIDENCE = "priority_then_confidence"


_DEFAULT_ENTITY_TYPES: tuple[str, ...] = (
    "finding",
    "recommendation",
    "priority_action",
    "roadmap_initiative",
    "correlation",
)

NAVIGATION_CATALOG_VERSION = "repository-drilldown-navigation-v1"
TRUNCATION_CATALOG_VERSION = "repository-drilldown-truncation-v1"


@dataclass(frozen=True, slots=True)
class RepositoryDrilldownPolicy:
    policy_id: str = "repository-drilldowns"
    policy_version: str = "v1"
    included_assessment_heads: tuple[str, ...] = ()
    included_entity_types: tuple[str, ...] = _DEFAULT_ENTITY_TYPES
    maximum_finding_refs: int = 20
    maximum_recommendation_refs: int = 20
    maximum_priority_action_refs: int = 10
    maximum_roadmap_refs: int = 10
    maximum_correlation_refs: int = 10
    maximum_pattern_refs: int = 50
    maximum_observation_refs: int = 50
    maximum_technology_refs: int = 40
    entity_selection_policy: EntitySelectionPolicy = (
        EntitySelectionPolicy.SEVERITY_THEN_CONFIDENCE
    )
    severity_selection_policy: str = "calibrated_severity_then_confidence_then_head_then_rule_then_id"
    priority_selection_policy: str = "calibrated_priority_then_score_then_confidence_then_id"
    visibility_policy: VisibilityAggregationScope = VisibilityAggregationScope.MIXED_INTERNAL
    anonymization_policy: AnonymizationPolicy = AnonymizationPolicy.USE_PROVIDED_WHEN_SAFE
    canonical_report_link_policy: str = "opaque_logical_reference"
    limitation_policy: str = "repository_specific_plus_truncation"
    public_export_policy: str = "precheck_only"
    legacy_policy: LegacyDrilldownPolicy = LegacyDrilldownPolicy.LIMITED
    navigation_catalog_version: str = NAVIGATION_CATALOG_VERSION
    truncation_catalog_version: str = TRUNCATION_CATALOG_VERSION
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.policy_version.strip():
            raise ValueError("policy_id and policy_version are required")
        for name in (
            "maximum_finding_refs",
            "maximum_recommendation_refs",
            "maximum_priority_action_refs",
            "maximum_roadmap_refs",
            "maximum_correlation_refs",
            "maximum_pattern_refs",
            "maximum_observation_refs",
            "maximum_technology_refs",
        ):
            value = getattr(self, name)
            if value is None or value < 1:
                raise ValueError(f"{name} must be >= 1 (unbounded lists are prohibited)")
        forbidden = {
            "maturity_score",
            "health_score",
            "readiness_score",
            "ranking",
            "composite_score",
            "title_similarity",
        }
        blob = " ".join(
            [
                self.severity_selection_policy,
                self.priority_selection_policy,
                self.entity_selection_policy.value,
                *self.limitations,
            ]
        ).lower()
        for token in forbidden:
            if token in blob.replace("-", "_").replace(" ", "_"):
                raise ValueError(f"ranking/score/title configuration prohibited: {token}")
        object.__setattr__(
            self,
            "included_entity_types",
            tuple(sorted({item.strip().lower() for item in self.included_entity_types if item.strip()})),
        )
        object.__setattr__(
            self,
            "included_assessment_heads",
            tuple(sorted({item.strip() for item in self.included_assessment_heads if item.strip()})),
        )

    @property
    def policy_token(self) -> str:
        return (
            f"{self.policy_id}:{self.policy_version}:"
            f"find={self.maximum_finding_refs}:"
            f"rec={self.maximum_recommendation_refs}:"
            f"pa={self.maximum_priority_action_refs}:"
            f"legacy={self.legacy_policy.value}:"
            f"anon={self.anonymization_policy.value}:"
            f"{self.navigation_catalog_version}:"
            f"{self.truncation_catalog_version}"
        )
