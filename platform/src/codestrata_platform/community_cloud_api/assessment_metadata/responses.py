"""Assessment metadata response models (Slice 7.8)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.assessment_metadata.enums import (
    AssessmentMetadataIngestionStatus,
)
from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
)


@dataclass(frozen=True, slots=True)
class AssessmentMetadataResponse:
    """Deterministic acknowledgement — no metadata echo or raw identifiers."""

    status: AssessmentMetadataIngestionStatus
    safe_event_reference: str
    retry_status: str
    schema_version: str = COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "retry_status": self.retry_status,
            "safe_event_reference": self.safe_event_reference,
            "schema_version": self.schema_version,
            "status": self.status.value,
        }
