"""AI usage event-stream projection (Slice 8.3)."""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest

SCHEMA_NAME = "community-ai-usage"


def project_payload(request: AiUsageRequest) -> dict[str, Any]:
    """Allowlisted projection via ``request.to_stable_dict()``.

    Preserves every approved endpoint field verbatim, including
    ``event_id`` and the optional ``installation_id``, for private raw
    storage. Excludes nothing that is part of the endpoint contract and
    adds nothing beyond it.
    """

    return request.to_stable_dict()


def client_type_from_request(request: AiUsageRequest) -> str:
    return request.client.name
