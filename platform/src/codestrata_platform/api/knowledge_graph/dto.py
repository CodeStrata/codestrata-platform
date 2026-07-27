"""Knowledge graph API DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BuildKnowledgeGraphRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str = Field(min_length=1, max_length=160)
    projector_version: str = Field(default="1.0.0", min_length=1, max_length=64)
    projection_schema_version: str = Field(default="1.0", min_length=1, max_length=64)


class RebuildKnowledgeGraphRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    projector_version: str = Field(default="1.0.0", min_length=1, max_length=64)
    projection_schema_version: str = Field(default="1.0", min_length=1, max_length=64)


class KnowledgeGraphSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    repository_id: str
    assessment_id: str
    engineering_snapshot_id: str
    engineering_snapshot_version: int
    graph_version: int
    status: str
    projection_key: str
    projector_version: str
    node_count: int
    edge_count: int
    created_at: datetime
    completed_at: datetime | None


class KnowledgeGraphDetailsResponse(KnowledgeGraphSummaryResponse):
    organization_id: str
    workspace_id: str
    intelligence_revision: int
    projection_schema_version: str
    failure_reason: str | None = None
    created: bool | None = None
    idempotent: bool | None = None


class GraphNodeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    node_type: str
    canonical_type: str
    canonical_id: str
    display_name: str
    properties: dict[str, object] | None = None


class GraphEdgeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str


class GraphNeighborResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edge: GraphEdgeResponse
    node: GraphNodeResponse


class GraphPathRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(min_length=1, max_length=240)
    target_node_id: str = Field(min_length=1, max_length=240)
    max_depth: int = Field(default=5, ge=1, le=10)
    edge_types: list[str] | None = None
    max_paths: int = Field(default=20, ge=1, le=50)


class GraphPathResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_ids: list[str]
