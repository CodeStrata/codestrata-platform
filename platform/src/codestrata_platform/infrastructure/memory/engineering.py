"""In-memory engineering snapshot repository."""

from __future__ import annotations

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.aggregate import EngineeringSnapshot
from codestrata_platform.domain.engineering.enums import EngineeringSnapshotStatus
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.engineering.taxonomy import TechnologyTaxonomy


class InMemoryEngineeringSnapshotRepository:
    def __init__(self) -> None:
        self._items: dict[str, EngineeringSnapshot] = {}

    def get(self, snapshot_id: EngineeringSnapshotId) -> EngineeringSnapshot | None:
        item = self._items.get(snapshot_id.value)
        return item.snapshot() if item is not None else None

    def save(self, snapshot: EngineeringSnapshot) -> None:
        self._items[snapshot.snapshot_id.value] = snapshot.snapshot()

    def list_by_assessment(
        self,
        assessment_id: AssessmentId,
    ) -> tuple[EngineeringSnapshot, ...]:
        return tuple(
            item.snapshot()
            for item in sorted(
                (
                    item
                    for item in self._items.values()
                    if item.assessment_id == assessment_id
                ),
                key=lambda item: item.version.value,
            )
        )

    def get_latest_published(
        self,
        assessment_id: AssessmentId,
    ) -> EngineeringSnapshot | None:
        published = [
            item
            for item in self._items.values()
            if item.assessment_id == assessment_id
            and item.status is EngineeringSnapshotStatus.PUBLISHED
        ]
        if not published:
            return None
        latest = max(published, key=lambda item: item.version.value)
        return latest.snapshot()

    def find_by_intelligence_revision(
        self,
        *,
        assessment_id: AssessmentId,
        assessment_intelligence_id: str,
        assessment_revision: int,
    ) -> EngineeringSnapshot | None:
        for item in self._items.values():
            if (
                item.assessment_id == assessment_id
                and item.assessment_intelligence_id == assessment_intelligence_id
                and item.assessment_revision == assessment_revision
            ):
                return item.snapshot()
        return None

    def latest_version_for_assessment(self, assessment_id: AssessmentId) -> int:
        versions = [
            item.version.value
            for item in self._items.values()
            if item.assessment_id == assessment_id
        ]
        return max(versions) if versions else 0


class InMemoryEngineeringTaxonomyRepository:
    def get_technology_taxonomy(self) -> TechnologyTaxonomy:
        return TechnologyTaxonomy()
