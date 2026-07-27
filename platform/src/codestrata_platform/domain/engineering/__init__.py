"""Canonical Engineering Intelligence Model (CEIM)."""

from __future__ import annotations

from codestrata_platform.domain.engineering.aggregate import EngineeringSnapshot
from codestrata_platform.domain.engineering.enums import (
    EngineeringCategory,
    EngineeringMetricKind,
    EngineeringRelationshipType,
    EngineeringSeverity,
    EngineeringSnapshotStatus,
    EvidenceKind,
)
from codestrata_platform.domain.engineering.ids import (
    EngineeringComponentId,
    EngineeringEvidenceId,
    EngineeringFindingId,
    EngineeringMetricId,
    EngineeringRecommendationId,
    EngineeringRelationshipId,
    EngineeringSnapshotId,
    EngineeringTechnologyId,
)
from codestrata_platform.domain.engineering.ports import (
    EngineeringSnapshotRepository,
    EngineeringTaxonomyRepository,
)
from codestrata_platform.domain.engineering.taxonomy import (
    CANONICAL_TECHNOLOGIES,
    TechnologyTaxonomy,
    normalize_technology_name,
)
from codestrata_platform.domain.engineering.value_objects import (
    EngineeringComponent,
    EngineeringEvidence,
    EngineeringFinding,
    EngineeringMetric,
    EngineeringRecommendation,
    EngineeringRelationship,
    EngineeringSnapshotVersion,
    EngineeringTag,
    EngineeringTechnology,
    RiskSummaryItem,
)

__all__ = [
    "CANONICAL_TECHNOLOGIES",
    "EngineeringCategory",
    "EngineeringComponent",
    "EngineeringComponentId",
    "EngineeringEvidence",
    "EngineeringEvidenceId",
    "EngineeringFinding",
    "EngineeringFindingId",
    "EngineeringMetric",
    "EngineeringMetricId",
    "EngineeringMetricKind",
    "EngineeringRecommendation",
    "EngineeringRecommendationId",
    "EngineeringRelationship",
    "EngineeringRelationshipId",
    "EngineeringRelationshipType",
    "EngineeringSeverity",
    "EngineeringSnapshot",
    "EngineeringSnapshotId",
    "EngineeringSnapshotRepository",
    "EngineeringSnapshotStatus",
    "EngineeringSnapshotVersion",
    "EngineeringTag",
    "EngineeringTaxonomyRepository",
    "EngineeringTechnology",
    "EngineeringTechnologyId",
    "EvidenceKind",
    "RiskSummaryItem",
    "TechnologyTaxonomy",
    "normalize_technology_name",
]
