"""Assessment metadata event-stream projection (Slice 8.3)."""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)

SCHEMA_NAME = "community-assessment-metadata"


def project_payload(request: AssessmentMetadataRequest) -> dict[str, Any]:
    """Allowlisted projection via ``request.to_stable_dict()``.

    Preserves every approved endpoint field verbatim, including
    ``event_id`` and the optional ``installation_id``, for private raw
    storage. Excludes nothing that is part of the endpoint contract and
    adds nothing beyond it.
    """

    return request.to_stable_dict()


def client_type_from_request(request: AssessmentMetadataRequest) -> str:
    return request.client.name
