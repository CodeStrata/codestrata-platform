"""Engineering relationship helpers (model only — no graph storage)."""

from __future__ import annotations

from codestrata_platform.domain.engineering.enums import EngineeringRelationshipType
from codestrata_platform.domain.engineering.ids import EngineeringRelationshipId
from codestrata_platform.domain.engineering.value_objects import EngineeringRelationship


def relationship(
    *,
    relationship_type: EngineeringRelationshipType,
    source_type: str,
    source_id: str,
    target_type: str,
    target_id: str,
) -> EngineeringRelationship:
    return EngineeringRelationship(
        relationship_id=EngineeringRelationshipId.generate(),
        relationship_type=relationship_type,
        source_type=source_type,
        source_id=source_id,
        target_type=target_type,
        target_id=target_id,
    )
