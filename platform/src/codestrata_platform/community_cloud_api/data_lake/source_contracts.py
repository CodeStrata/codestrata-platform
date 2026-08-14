"""Source contract descriptor model for Data Lake envelope streams (Slice 8.3).

A :class:`SourceContractDescriptor` binds one :class:`~.enums.EventStream` to
the endpoint request model, allowlisted client types, and projection/
extraction callables that :mod:`.envelope_registry` looks up when building an
envelope from a typed request. This module defines the shape only — the
concrete instances live in :mod:`.envelope_registry`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.validation.models import CommunityApiRequestModel


class SourceContractError(ValueError):
    """Raised when a source contract descriptor is malformed."""


@dataclass(frozen=True, slots=True)
class SourceContractDescriptor:
    """Deterministic binding between one event stream and its endpoint contract."""

    event_stream: EventStream
    schema_name: str
    schema_version: str
    policy_id: str
    request_model: type[CommunityApiRequestModel]
    allowed_client_types: frozenset[str]
    project_payload: Callable[[CommunityApiRequestModel], dict[str, Any]]
    client_type_extractor: Callable[[CommunityApiRequestModel], str]
    catalog_versions: Mapping[str, str] = field(default_factory=dict)
    # When set, envelope source_contract.schema_version may be any of these
    # (request-driven). Default is the singleton {schema_version}.
    supported_schema_versions: frozenset[str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event_stream, EventStream):
            raise SourceContractError("event_stream must be an EventStream member")
        if not self.schema_name or not self.schema_name.strip():
            raise SourceContractError("schema_name is required")
        if not self.schema_version or not self.schema_version.strip():
            raise SourceContractError("schema_version is required")
        if not self.policy_id or ":" not in self.policy_id:
            raise SourceContractError("policy_id must be a full URN (id:version)")
        if not isinstance(self.request_model, type) or not issubclass(
            self.request_model, CommunityApiRequestModel
        ):
            raise SourceContractError("request_model must subclass CommunityApiRequestModel")
        if not self.allowed_client_types:
            raise SourceContractError("allowed_client_types must not be empty")
        object.__setattr__(
            self, "allowed_client_types", frozenset(self.allowed_client_types)
        )
        object.__setattr__(self, "catalog_versions", dict(self.catalog_versions))
        supported = self.supported_schema_versions
        if supported is None:
            supported = frozenset({self.schema_version})
        else:
            supported = frozenset(supported)
        if self.schema_version not in supported:
            raise SourceContractError(
                "schema_version must be included in supported_schema_versions"
            )
        object.__setattr__(self, "supported_schema_versions", supported)

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "allowed_client_types": sorted(self.allowed_client_types),
            "catalog_versions": dict(sorted(self.catalog_versions.items())),
            "event_stream": self.event_stream.value,
            "policy_id": self.policy_id,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "supported_schema_versions": sorted(self.supported_schema_versions or ()),
        }
