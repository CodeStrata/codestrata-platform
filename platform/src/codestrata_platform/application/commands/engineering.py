"""Engineering snapshot application commands."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.intelligence.ids import AssessmentIntelligenceId


@dataclass(frozen=True, slots=True)
class BuildEngineeringSnapshotCommand:
    assessment_id: AssessmentId
    intelligence_id: AssessmentIntelligenceId | None = None
    publish: bool = True


@dataclass(frozen=True, slots=True)
class PublishEngineeringSnapshotCommand:
    snapshot_id: EngineeringSnapshotId


@dataclass(frozen=True, slots=True)
class SupersedeEngineeringSnapshotCommand:
    snapshot_id: EngineeringSnapshotId
