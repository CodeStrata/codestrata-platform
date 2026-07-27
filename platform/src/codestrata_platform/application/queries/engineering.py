"""Engineering snapshot application queries."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.enums import EngineeringSeverity
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId


@dataclass(frozen=True, slots=True)
class GetEngineeringSnapshotQuery:
    snapshot_id: EngineeringSnapshotId


@dataclass(frozen=True, slots=True)
class GetLatestEngineeringSnapshotQuery:
    assessment_id: AssessmentId


@dataclass(frozen=True, slots=True)
class ListEngineeringSnapshotsQuery:
    assessment_id: AssessmentId | None = None


@dataclass(frozen=True, slots=True)
class GetTechnologyInventoryQuery:
    snapshot_id: EngineeringSnapshotId | None = None
    assessment_id: AssessmentId | None = None


@dataclass(frozen=True, slots=True)
class GetRiskInventoryQuery:
    snapshot_id: EngineeringSnapshotId | None = None
    assessment_id: AssessmentId | None = None
    severity: EngineeringSeverity | None = None


@dataclass(frozen=True, slots=True)
class GetRecommendationInventoryQuery:
    snapshot_id: EngineeringSnapshotId | None = None
    assessment_id: AssessmentId | None = None


@dataclass(frozen=True, slots=True)
class GetMetricInventoryQuery:
    snapshot_id: EngineeringSnapshotId | None = None
    assessment_id: AssessmentId | None = None


@dataclass(frozen=True, slots=True)
class GetFindingInventoryQuery:
    snapshot_id: EngineeringSnapshotId | None = None
    assessment_id: AssessmentId | None = None
    severity: EngineeringSeverity | None = None
