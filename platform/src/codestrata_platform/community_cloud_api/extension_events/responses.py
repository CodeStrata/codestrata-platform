"""Extension event response models (Slice 7.10)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.extension_events.enums import (
    ExtensionEventIngestionStatus,
)
from codestrata_platform.community_cloud_api.extension_events.policy import (
    COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
)


@dataclass(frozen=True, slots=True)
class ExtensionEventResponse:
    status: ExtensionEventIngestionStatus
    safe_event_reference: str
    retry_status: str
    schema_version: str = COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "retry_status": self.retry_status,
            "safe_event_reference": self.safe_event_reference,
            "schema_version": self.schema_version,
            "status": self.status.value,
        }
