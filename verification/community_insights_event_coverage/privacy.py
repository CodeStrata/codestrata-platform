"""Privacy allow/deny helpers."""

from __future__ import annotations

from typing import Any

from verification.community_insights_event_coverage.schemas import PRIVACY_FORBIDDEN


def privacy_matrix() -> dict[str, Any]:
    return {
        "forbidden": list(PRIVACY_FORBIDDEN),
        "allowed_identity": "payload.installation_id_per_existing_policy",
        "allowed_model_dimension": "payload.usage.model_family",
        "forbidden_model_dimension": "model_id",
    }
