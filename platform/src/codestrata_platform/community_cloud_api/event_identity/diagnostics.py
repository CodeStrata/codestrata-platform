"""Safe event-identity diagnostics for future handlers/logging."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.event_identity.models import RetryDecision


@dataclass(frozen=True, slots=True)
class EventIdentityDiagnostic:
    """Safe diagnostic — never includes raw event_id or fingerprints."""

    safe_event_reference: str
    retry_status: str
    identity_policy_version: str
    source_event_type: str | None = None

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "identity_policy_version": self.identity_policy_version,
            "retry_status": self.retry_status,
            "safe_event_reference": self.safe_event_reference,
        }
        if self.source_event_type is not None:
            payload["source_event_type"] = self.source_event_type
        return {key: payload[key] for key in sorted(payload)}


def build_event_identity_diagnostic(
    decision: RetryDecision,
    *,
    identity_policy_version: str,
    source_event_type: str | None = None,
) -> EventIdentityDiagnostic:
    return EventIdentityDiagnostic(
        safe_event_reference=decision.safe_event_reference,
        retry_status=decision.status.value,
        identity_policy_version=identity_policy_version,
        source_event_type=source_event_type,
    )
