"""Telemetry event-stream projection (Slice 8.3)."""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.telemetry.models import TelemetryIngestionRequest

SCHEMA_NAME = "community-telemetry"


def project_payload(request: TelemetryIngestionRequest) -> dict[str, Any]:
    """Allowlisted projection via ``request.to_stable_dict()``.

    Preserves every approved endpoint field verbatim, including
    ``event_id`` and the optional ``installation_id``, for private raw
    storage. Excludes nothing that is part of the endpoint contract and
    adds nothing beyond it — this function never touches transport-only
    fields (there are none on this model).
    """

    return request.to_stable_dict()


def client_type_from_request(request: TelemetryIngestionRequest) -> str:
    return request.client.name
