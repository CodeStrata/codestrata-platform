"""Telemetry ingestion response models (Slice 7.7)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.telemetry.enums import (
    TelemetryIngestionStatus,
)
from codestrata_platform.community_cloud_api.telemetry.policy import (
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
)


@dataclass(frozen=True, slots=True)
class TelemetryIngestionResponse:
    """Deterministic acknowledgement — no raw ids, fingerprints, or storage claims."""

    status: TelemetryIngestionStatus
    safe_event_reference: str
    retry_status: str
    schema_version: str = COMMUNITY_TELEMETRY_SCHEMA_VERSION

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "retry_status": self.retry_status,
            "safe_event_reference": self.safe_event_reference,
            "schema_version": self.schema_version,
            "status": self.status.value,
        }
