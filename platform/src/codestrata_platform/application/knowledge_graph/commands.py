"""Knowledge graph application commands."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId


@dataclass(frozen=True, slots=True)
class BuildKnowledgeGraphCommand:
    snapshot_id: EngineeringSnapshotId
    projector_version: str = "1.0.0"
    projection_schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class RebuildKnowledgeGraphCommand:
    graph_id: KnowledgeGraphId
    projector_version: str = "1.0.0"
    projection_schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class SupersedeKnowledgeGraphCommand:
    graph_id: KnowledgeGraphId


@dataclass(frozen=True, slots=True)
class FailKnowledgeGraphProjectionCommand:
    graph_id: KnowledgeGraphId
    reason: str
