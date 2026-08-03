"""CLI event response models (Slice 7.9)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.cli_events.enums import CliEventIngestionStatus
from codestrata_platform.community_cloud_api.cli_events.policy import (
    COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
)


@dataclass(frozen=True, slots=True)
class CliEventResponse:
    status: CliEventIngestionStatus
    safe_event_reference: str
    retry_status: str
    schema_version: str = COMMUNITY_CLI_EVENT_SCHEMA_VERSION

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "retry_status": self.retry_status,
            "safe_event_reference": self.safe_event_reference,
            "schema_version": self.schema_version,
            "status": self.status.value,
        }
