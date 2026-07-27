"""Ports for Canonical Engineering Intelligence Model persistence."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.aggregate import EngineeringSnapshot
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.engineering.taxonomy import TechnologyTaxonomy


class EngineeringSnapshotRepository(Protocol):
    def get(self, snapshot_id: EngineeringSnapshotId) -> EngineeringSnapshot | None: ...

    def save(self, snapshot: EngineeringSnapshot) -> None: ...

    def list_by_assessment(
        self,
        assessment_id: AssessmentId,
    ) -> tuple[EngineeringSnapshot, ...]: ...

    def get_latest_published(
        self,
        assessment_id: AssessmentId,
    ) -> EngineeringSnapshot | None: ...

    def find_by_intelligence_revision(
        self,
        *,
        assessment_id: AssessmentId,
        assessment_intelligence_id: str,
        assessment_revision: int,
    ) -> EngineeringSnapshot | None: ...

    def latest_version_for_assessment(self, assessment_id: AssessmentId) -> int: ...


class EngineeringTaxonomyRepository(Protocol):
    def get_technology_taxonomy(self) -> TechnologyTaxonomy: ...
