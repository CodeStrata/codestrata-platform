"""AI usage response models (Slice 7.11)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.ai_usage.enums import AiUsageIngestionStatus
from codestrata_platform.community_cloud_api.ai_usage.policy import (
    COMMUNITY_AI_USAGE_SCHEMA_VERSION,
)


@dataclass(frozen=True, slots=True)
class AiUsageResponse:
    status: AiUsageIngestionStatus
    safe_event_reference: str
    retry_status: str
    schema_version: str = COMMUNITY_AI_USAGE_SCHEMA_VERSION

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "retry_status": self.retry_status,
            "safe_event_reference": self.safe_event_reference,
            "schema_version": self.schema_version,
            "status": self.status.value,
        }
