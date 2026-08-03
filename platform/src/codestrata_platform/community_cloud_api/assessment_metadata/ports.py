"""Assessment metadata sink ports — persistence-neutral (Slice 7.8)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from codestrata_platform.community_cloud_api.assessment_metadata.enums import (
    AssessmentMetadataSinkStatus,
)
from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentArtifactMetadata,
    AssessmentExecutionMetadata,
    AssessmentMetadataBlock,
    RepositoryMetadata,
)
from codestrata_platform.community_cloud_api.telemetry.models import TelemetryClient


@dataclass(frozen=True, slots=True)
class ValidatedAssessmentMetadataEvent:
    """Sink-facing event — no raw event_id, installation_id, or request body."""

    event_key: str
    safe_event_reference: str
    schema_version: str
    client: TelemetryClient
    assessment: AssessmentMetadataBlock
    repository: RepositoryMetadata
    execution: AssessmentExecutionMetadata
    artifacts: AssessmentArtifactMetadata
    identity_policy_version: str
    metadata_policy_version: str

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "artifacts": self.artifacts.to_stable_dict(),
            "assessment": self.assessment.to_stable_dict(),
            "client": self.client.to_stable_dict(),
            "event_key": self.event_key,
            "execution": self.execution.to_stable_dict(),
            "identity_policy_version": self.identity_policy_version,
            "metadata_policy_version": self.metadata_policy_version,
            "repository": self.repository.to_stable_dict(),
            "safe_event_reference": self.safe_event_reference,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class AssessmentMetadataSinkResult:
    status: AssessmentMetadataSinkStatus
    reason: str = ""

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": self.status.value}
        if self.reason:
            payload["reason"] = self.reason
        return {key: payload[key] for key in sorted(payload)}


class AssessmentMetadataSink(Protocol):
    def accept(
        self, event: ValidatedAssessmentMetadataEvent
    ) -> AssessmentMetadataSinkResult: ...


class UnavailableAssessmentMetadataSink:
    """Default production sink — never claims durable acceptance."""

    def accept(
        self, event: ValidatedAssessmentMetadataEvent
    ) -> AssessmentMetadataSinkResult:
        _ = event
        return AssessmentMetadataSinkResult(
            status=AssessmentMetadataSinkStatus.UNAVAILABLE,
            reason="assessment_metadata_sink_unavailable",
        )


@dataclass
class InMemoryAssessmentMetadataSink:
    """Test-only accepting sink — not a production adapter."""

    events: list[ValidatedAssessmentMetadataEvent] = field(default_factory=list)
    fail_next: bool = False
    reject_next: bool = False

    def accept(
        self, event: ValidatedAssessmentMetadataEvent
    ) -> AssessmentMetadataSinkResult:
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("simulated_metadata_sink_failure")
        if self.reject_next:
            self.reject_next = False
            return AssessmentMetadataSinkResult(
                status=AssessmentMetadataSinkStatus.REJECTED,
                reason="assessment_metadata_rejected",
            )
        self.events.append(event)
        return AssessmentMetadataSinkResult(
            status=AssessmentMetadataSinkStatus.ACCEPTED, reason="accepted"
        )

    def clear(self) -> None:
        self.events.clear()
