"""Route helpers for attaching request schemas.

Slice 7.3 adds no production event endpoints. Test suites may register private
fixture routes via ``RouteRegistry.register(..., request_schema=...)``.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.registry import RouteRegistry, RouteSpec
from codestrata_platform.community_cloud_api.validation.models import (
    NO_BODY_SCHEMA,
    RequestSchemaDescriptor,
)


def attach_no_body_schema(registry: RouteRegistry, spec: RouteSpec) -> None:
    """Ensure a registered route forbids request bodies (e.g. health)."""

    registry.bind_request_schema(spec, NO_BODY_SCHEMA)


def require_request_schema(
    descriptor: RequestSchemaDescriptor,
) -> RequestSchemaDescriptor:
    """Validate descriptor identity before registration (pass-through helper)."""

    _ = descriptor.identity_key()
    return descriptor
