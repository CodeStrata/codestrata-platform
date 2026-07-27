"""Deterministic graph identity helpers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.shared.ids import PlatformId

_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,240}$")


def _stable_token(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]
    return digest


@dataclass(frozen=True, slots=True)
class KnowledgeGraphId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> KnowledgeGraphId:
        return cls(PlatformId.generate(prefix="eng-graph").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class GraphProjectionId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> GraphProjectionId:
        return cls(PlatformId.generate(prefix="graph-projection").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class GraphNodeId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or not _TOKEN.match(compact):
            raise InvalidValueError(
                "Graph node id is invalid",
                reason_code="invalid_graph_node_id",
            )
        object.__setattr__(self, "value", compact)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class GraphEdgeId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or not _TOKEN.match(compact):
            raise InvalidValueError(
                "Graph edge id is invalid",
                reason_code="invalid_graph_edge_id",
            )
        object.__setattr__(self, "value", compact)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class GraphProjectionKey:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "projection key must be non-blank",
                reason_code="empty_projection_key",
            )
        if len(compact) > 128:
            raise InvalidValueError(
                "projection key exceeds maximum length",
                reason_code="projection_key_too_long",
            )
        object.__setattr__(self, "value", compact)

    @classmethod
    def from_parts(
        cls,
        *,
        engineering_snapshot_id: str,
        engineering_snapshot_version: int,
        projection_schema_version: str,
        projector_version: str,
    ) -> GraphProjectionKey:
        digest = hashlib.sha256(
            "|".join(
                [
                    engineering_snapshot_id.strip(),
                    str(engineering_snapshot_version),
                    projection_schema_version.strip(),
                    projector_version.strip(),
                ]
            ).encode("utf-8")
        ).hexdigest()
        return cls(digest)


def deterministic_graph_id(
    *,
    repository_id: str,
    snapshot_id: str,
    snapshot_version: int,
    projector_version: str,
) -> KnowledgeGraphId:
    token = _stable_token(
        repository_id,
        snapshot_id,
        str(snapshot_version),
        projector_version,
    )
    return KnowledgeGraphId(f"eng-graph:{token}")


def deterministic_node_id(
    *,
    snapshot_id: str,
    node_type: str,
    canonical_id: str,
) -> GraphNodeId:
    token = _stable_token(snapshot_id, node_type, canonical_id)
    return GraphNodeId(f"graph-node:{token}")


def deterministic_edge_id(
    *,
    graph_id: str,
    source_node_id: str,
    edge_type: str,
    target_node_id: str,
    discriminator: str = "",
) -> GraphEdgeId:
    token = _stable_token(
        graph_id,
        source_node_id,
        edge_type,
        target_node_id,
        discriminator,
    )
    return GraphEdgeId(f"graph-edge:{token}")
