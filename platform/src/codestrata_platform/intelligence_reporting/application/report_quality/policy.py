"""ReportQualityPolicy and IntelligenceInterpretationPolicyBundle."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.domain.enums import ReportScope


class LegacyReportQualityPolicy(StrEnum):
    INCLUDE_LIMITED = "include_limited"
    EXCLUDE = "exclude"


class SourceDiversityMode(StrEnum):
    """How representation concentration is interpreted by report scope."""

    MATERIAL_FOR_PUBLIC = "material_for_public"
    INFORMATIONAL_FOR_CUSTOMER = "informational_for_customer"
    FIXTURE_EXPLICIT_FOR_VALIDATION = "fixture_explicit_for_validation"


HEAD_CATALOG_VERSION = "commercial-head-catalog-v1"
NORMALIZATION_VERSION = "technology-normalization-v1"
PATTERN_IDENTITY_CATALOG_VERSION = "recurring-pattern-identity-v1"
ACTION_IDENTITY_CATALOG_VERSION = "modernization-action-identity-v1"
STATEMENT_TEMPLATE_TECH = "technology-distribution-statement-v1"
STATEMENT_TEMPLATE_PATTERN = "recurring-pattern-statement-v1"
STATEMENT_TEMPLATE_MODERNIZATION = "modernization-observation-statement-v1"
STATEMENT_TEMPLATE_QUALITY = "report-quality-limitation-statement-v1"

MATERIAL_SECTIONS_DEFAULT: tuple[str, ...] = (
    "dataset",
    "repository_population",
    "technology_distribution",
    "capability_comparison",
    "assessment_head_distribution",
)
OPTIONAL_SECTIONS_DEFAULT: tuple[str, ...] = (
    "recurring_patterns",
    "modernization_observations",
)

_FORBIDDEN_NUMERIC = (
    "confidence_percentage",
    "accuracy_percentage",
    "precision",
    "recall",
    "probability",
    "weighted_average",
    "composite_score",
    "maturity_score",
    "health_score",
    "readiness_score",
    "ranking",
)


def _sha24(material: str) -> str:
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def _stable_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True, slots=True)
class ReportQualityPolicy:
    policy_id: str = "report-quality"
    policy_version: str = "v1"
    confidence_policy_version: str = "report-confidence-v1"
    limitation_policy_version: str = "dataset-limitation-v1"
    minimum_repository_count: int = 2
    minimum_comparable_repository_count: int = 2
    small_sample_threshold: int = 3
    high_minimum_comparable_repository_count: int = 5
    material_sections: tuple[str, ...] = MATERIAL_SECTIONS_DEFAULT
    optional_sections: tuple[str, ...] = OPTIONAL_SECTIONS_DEFAULT
    source_diversity_policy: SourceDiversityMode = SourceDiversityMode.MATERIAL_FOR_PUBLIC
    schema_compatibility_policy: str = "canonical_or_legacy_limited"
    assessment_age_policy: str = "deferred_without_consistent_timestamps"
    coverage_policy: str = "canonical_assessment_coverage"
    section_materiality_policy: str = "material_caps_optional_discloses"
    legacy_policy: LegacyReportQualityPolicy = LegacyReportQualityPolicy.INCLUDE_LIMITED
    visibility_policy: VisibilityAggregationScope = VisibilityAggregationScope.MIXED_INTERNAL
    limitation_deduplication_policy: str = "category_subject_scope"
    non_temporal_blocks_high: bool = True
    high_requires_no_material_limitations: bool = True
    high_allows_weakest_moderate: bool = True
    selection_bias_scopes: tuple[ReportScope, ...] = (
        ReportScope.PUBLIC_OSS_DATASET,
        ReportScope.INTERNAL_VALIDATION_DATASET,
    )
    language_concentration_threshold: float = 0.75
    fixture_concentration_threshold: float = 0.5
    limitation_statement_template_version: str = STATEMENT_TEMPLATE_QUALITY
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.minimum_repository_count < 0:
            raise ValueError("minimum_repository_count must be >= 0")
        if self.minimum_comparable_repository_count < 0:
            raise ValueError("minimum_comparable_repository_count must be >= 0")
        if self.small_sample_threshold < 1:
            raise ValueError("small_sample_threshold must be >= 1")
        if self.high_minimum_comparable_repository_count < self.minimum_comparable_repository_count:
            raise ValueError(
                "high_minimum_comparable_repository_count must be >= "
                "minimum_comparable_repository_count"
            )
        if not (0.0 < self.language_concentration_threshold <= 1.0):
            raise ValueError("language_concentration_threshold must be in (0, 1]")
        if not (0.0 < self.fixture_concentration_threshold <= 1.0):
            raise ValueError("fixture_concentration_threshold must be in (0, 1]")
        if not self.policy_id.strip() or not self.policy_version.strip():
            raise ValueError("policy_id and policy_version are required")
        blob = " ".join(
            [
                self.confidence_policy_version,
                self.limitation_policy_version,
                self.coverage_policy,
                *self.limitations,
            ]
        ).lower()
        for token in _FORBIDDEN_NUMERIC:
            if token in blob.replace("-", "_").replace(" ", "_"):
                raise ValueError(f"numeric/score confidence configuration prohibited: {token}")
        object.__setattr__(
            self,
            "material_sections",
            tuple(sorted({item.strip() for item in self.material_sections if item.strip()})),
        )
        object.__setattr__(
            self,
            "optional_sections",
            tuple(sorted({item.strip() for item in self.optional_sections if item.strip()})),
        )
        object.__setattr__(
            self,
            "selection_bias_scopes",
            tuple(sorted(self.selection_bias_scopes, key=lambda item: item.value)),
        )

    @property
    def policy_token(self) -> str:
        return (
            f"{self.policy_id}:{self.policy_version}:"
            f"{self.confidence_policy_version}:{self.limitation_policy_version}:"
            f"min_repo={self.minimum_repository_count}:"
            f"min_comp={self.minimum_comparable_repository_count}:"
            f"small={self.small_sample_threshold}:"
            f"high_min={self.high_minimum_comparable_repository_count}:"
            f"legacy={self.legacy_policy.value}:"
            f"diversity={self.source_diversity_policy.value}"
        )

    def diversity_mode_for_scope(self, scope: ReportScope) -> SourceDiversityMode:
        if scope is ReportScope.INTERNAL_VALIDATION_DATASET:
            return SourceDiversityMode.FIXTURE_EXPLICIT_FOR_VALIDATION
        if scope in {
            ReportScope.CUSTOMER_PORTFOLIO,
            ReportScope.CUSTOMER_WORKSPACE,
            ReportScope.DESIGN_PARTNER_DATASET,
        }:
            return SourceDiversityMode.INFORMATIONAL_FOR_CUSTOMER
        if scope is ReportScope.PUBLIC_OSS_DATASET:
            return SourceDiversityMode.MATERIAL_FOR_PUBLIC
        return self.source_diversity_policy


@dataclass(frozen=True, slots=True)
class CatalogVersions:
    head_catalog_version: str = HEAD_CATALOG_VERSION
    normalization_version: str = NORMALIZATION_VERSION
    pattern_identity_catalog_version: str = PATTERN_IDENTITY_CATALOG_VERSION
    action_identity_catalog_version: str = ACTION_IDENTITY_CATALOG_VERSION
    statement_template_versions: tuple[tuple[str, str], ...] = (
        ("technology", STATEMENT_TEMPLATE_TECH),
        ("recurring_pattern", STATEMENT_TEMPLATE_PATTERN),
        ("modernization", STATEMENT_TEMPLATE_MODERNIZATION),
        ("report_quality", STATEMENT_TEMPLATE_QUALITY),
    )

    def __post_init__(self) -> None:
        templates = tuple(
            sorted(
                ((key.strip(), value.strip()) for key, value in self.statement_template_versions),
                key=lambda item: item[0],
            )
        )
        object.__setattr__(self, "statement_template_versions", templates)

    def identity_material(self) -> dict[str, object]:
        return {
            "head_catalog_version": self.head_catalog_version,
            "normalization_version": self.normalization_version,
            "pattern_identity_catalog_version": self.pattern_identity_catalog_version,
            "action_identity_catalog_version": self.action_identity_catalog_version,
            "statement_template_versions": [
                {"section": key, "version": value}
                for key, value in self.statement_template_versions
            ],
        }


@dataclass(frozen=True, slots=True)
class IntelligenceInterpretationPolicyBundle:
    """Deterministic interpretation-policy identity for report ID material."""

    bundle_id: str
    bundle_version: str = "v1"
    technology_policy_token: str = ""
    capability_policy_token: str = ""
    recurring_pattern_policy_token: str = ""
    modernization_policy_token: str = ""
    report_quality_policy_token: str = ""
    repository_drilldown_policy_token: str = ""
    website_export_policy_token: str = ""
    catalog_versions: CatalogVersions = field(default_factory=CatalogVersions)

    def __post_init__(self) -> None:
        expected = build_interpretation_policy_bundle_id(
            bundle_version=self.bundle_version,
            technology_policy_token=self.technology_policy_token,
            capability_policy_token=self.capability_policy_token,
            recurring_pattern_policy_token=self.recurring_pattern_policy_token,
            modernization_policy_token=self.modernization_policy_token,
            report_quality_policy_token=self.report_quality_policy_token,
            repository_drilldown_policy_token=self.repository_drilldown_policy_token,
            website_export_policy_token=self.website_export_policy_token,
            catalog_versions=self.catalog_versions,
        )
        if self.bundle_id != expected:
            raise ValueError("bundle_id does not match component tokens")


def build_interpretation_policy_bundle_id(
    *,
    technology_policy_token: str,
    capability_policy_token: str,
    recurring_pattern_policy_token: str,
    modernization_policy_token: str,
    report_quality_policy_token: str,
    repository_drilldown_policy_token: str = "",
    website_export_policy_token: str = "",
    bundle_version: str = "v1",
    catalog_versions: CatalogVersions | None = None,
) -> str:
    catalogs = catalog_versions or CatalogVersions()
    material = _stable_json(
        {
            "bundle_version": bundle_version.strip(),
            "technology_policy_token": technology_policy_token.strip(),
            "capability_policy_token": capability_policy_token.strip(),
            "recurring_pattern_policy_token": recurring_pattern_policy_token.strip(),
            "modernization_policy_token": modernization_policy_token.strip(),
            "report_quality_policy_token": report_quality_policy_token.strip(),
            "repository_drilldown_policy_token": repository_drilldown_policy_token.strip(),
            "website_export_policy_token": website_export_policy_token.strip(),
            "catalog_versions": catalogs.identity_material(),
        }
    )
    return f"interp-bundle:{_sha24(material)}"


def build_interpretation_policy_bundle(
    *,
    technology_policy_token: str,
    capability_policy_token: str,
    recurring_pattern_policy_token: str,
    modernization_policy_token: str,
    report_quality_policy_token: str,
    repository_drilldown_policy_token: str = "",
    website_export_policy_token: str = "",
    bundle_version: str = "v1",
    catalog_versions: CatalogVersions | None = None,
) -> IntelligenceInterpretationPolicyBundle:
    catalogs = catalog_versions or CatalogVersions()
    bundle_id = build_interpretation_policy_bundle_id(
        bundle_version=bundle_version,
        technology_policy_token=technology_policy_token,
        capability_policy_token=capability_policy_token,
        recurring_pattern_policy_token=recurring_pattern_policy_token,
        modernization_policy_token=modernization_policy_token,
        report_quality_policy_token=report_quality_policy_token,
        repository_drilldown_policy_token=repository_drilldown_policy_token,
        website_export_policy_token=website_export_policy_token,
        catalog_versions=catalogs,
    )
    return IntelligenceInterpretationPolicyBundle(
        bundle_id=bundle_id,
        bundle_version=bundle_version,
        technology_policy_token=technology_policy_token.strip(),
        capability_policy_token=capability_policy_token.strip(),
        recurring_pattern_policy_token=recurring_pattern_policy_token.strip(),
        modernization_policy_token=modernization_policy_token.strip(),
        report_quality_policy_token=report_quality_policy_token.strip(),
        repository_drilldown_policy_token=repository_drilldown_policy_token.strip(),
        website_export_policy_token=website_export_policy_token.strip(),
        catalog_versions=catalogs,
    )
