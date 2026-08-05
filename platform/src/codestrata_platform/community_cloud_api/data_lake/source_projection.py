"""Dispatch a typed endpoint request to its registered stream projector (Slice 8.3)."""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.envelope_registry import get_source_contract
from codestrata_platform.community_cloud_api.validation.models import CommunityApiRequestModel


class SourceProjectionError(ValueError):
    """Raised when a request cannot be projected for its declared stream."""


def _resolve_and_check(
    event_stream: EventStream | str, request: CommunityApiRequestModel
):
    descriptor = get_source_contract(event_stream)
    if not isinstance(request, descriptor.request_model):
        raise SourceProjectionError(
            f"request type {type(request).__name__} does not match "
            f"stream contract {descriptor.event_stream.value!r}"
        )
    return descriptor


def project_request_payload(
    event_stream: EventStream | str, request: CommunityApiRequestModel
) -> dict[str, Any]:
    """Allowlisted payload projection for ``request`` under ``event_stream``."""

    descriptor = _resolve_and_check(event_stream, request)
    return descriptor.project_payload(request)


def extract_client_type(
    event_stream: EventStream | str, request: CommunityApiRequestModel
) -> str:
    """Extract and validate the client type for ``request`` under ``event_stream``."""

    descriptor = _resolve_and_check(event_stream, request)
    client_type = descriptor.client_type_extractor(request)
    if client_type not in descriptor.allowed_client_types:
        raise SourceProjectionError(f"client_type not allowed for stream: {client_type!r}")
    return client_type
