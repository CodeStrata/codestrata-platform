"""Graph node value objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphNodeType

_MAX_PROPERTIES = 50
_MAX_STRING = 2000
_SECRET_MARKERS = ("password", "secret", "token", "api_key", "private_key", "credential")


def _validate_properties(properties: Mapping[str, Any] | None) -> dict[str, Any]:
    if not properties:
        return {}
    if len(properties) > _MAX_PROPERTIES:
        raise InvalidValueError(
            f"Graph properties may contain at most {_MAX_PROPERTIES} keys",
            reason_code="graph_properties_too_large",
        )
    normalized: dict[str, Any] = {}
    for key, value in dict(properties).items():
        compact_key = str(key).strip()
        if not compact_key:
            raise InvalidValueError(
                "Graph property keys must be non-blank",
                reason_code="empty_graph_property_key",
            )
        if any(marker in compact_key.lower() for marker in _SECRET_MARKERS):
            raise InvalidValueError(
                f"Graph property key '{compact_key}' is not allowed",
                reason_code="secret_bearing_graph_property",
            )
        if isinstance(value, str) and len(value) > _MAX_STRING:
            raise InvalidValueError(
                "Graph property string exceeds maximum length",
                reason_code="graph_property_too_long",
            )
        if isinstance(value, list) and len(value) > 100:
            raise InvalidValueError(
                "Graph property list exceeds maximum length",
                reason_code="graph_property_list_too_large",
            )
        if not isinstance(value, (str, int, float, bool, list, type(None))):
            raise InvalidValueError(
                "Graph property value type is not supported",
                reason_code="unsupported_graph_property_type",
            )
        if isinstance(value, list) and not all(isinstance(item, str) for item in value):
            raise InvalidValueError(
                "Graph property lists may contain only strings",
                reason_code="invalid_graph_property_list",
            )
        normalized[compact_key] = value
    return dict(sorted(normalized.items()))


@dataclass(frozen=True, slots=True)
class GraphProperty:
    """Typed bounded graph property bag."""

    values: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _validate_properties(self.values))


@dataclass(frozen=True, slots=True)
class GraphSourceReference:
    snapshot_id: str
    canonical_type: str
    canonical_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_id", self.snapshot_id.strip())
        object.__setattr__(self, "canonical_type", self.canonical_type.strip())
        object.__setattr__(self, "canonical_id", self.canonical_id.strip())
        if not self.snapshot_id or not self.canonical_type or not self.canonical_id:
            raise InvalidValueError(
                "Graph source reference fields must be non-blank",
                reason_code="invalid_graph_source_reference",
            )


@dataclass(frozen=True, slots=True)
class GraphNode:
    node_id: GraphNodeId
    node_type: GraphNodeType
    canonical_type: str
    canonical_id: str
    display_name: str
    properties: GraphProperty = field(default_factory=GraphProperty)
    source_reference: GraphSourceReference | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "canonical_type", self.canonical_type.strip())
        object.__setattr__(self, "canonical_id", self.canonical_id.strip())
        object.__setattr__(self, "display_name", self.display_name.strip())
        if not self.canonical_type or not self.canonical_id or not self.display_name:
            raise InvalidValueError(
                "Graph node identity fields must be non-blank",
                reason_code="invalid_graph_node",
            )
        if len(self.display_name) > _MAX_STRING:
            raise InvalidValueError(
                "Graph node display_name exceeds maximum length",
                reason_code="graph_node_display_name_too_long",
            )
