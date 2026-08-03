"""Internal AI usage diagnostics — never returned in API responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AiUsageDiagnostics:
    request_validated: bool
    identity_available: bool
    retry_status: str | None
    sink_status: str | None
    identity_record_status: str | None
    safe_event_reference: str | None
    schema_version: str
    policy_version: str
    capability_catalog_version: str
    provider_catalog_version: str
    model_catalog_version: str
    limitations: tuple[str, ...] = ()

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "capability_catalog_version": self.capability_catalog_version,
            "identity_available": self.identity_available,
            "limitations": list(self.limitations),
            "model_catalog_version": self.model_catalog_version,
            "policy_version": self.policy_version,
            "provider_catalog_version": self.provider_catalog_version,
            "request_validated": self.request_validated,
            "schema_version": self.schema_version,
        }
        if self.identity_record_status is not None:
            payload["identity_record_status"] = self.identity_record_status
        if self.retry_status is not None:
            payload["retry_status"] = self.retry_status
        if self.safe_event_reference is not None:
            payload["safe_event_reference"] = self.safe_event_reference
        if self.sink_status is not None:
            payload["sink_status"] = self.sink_status
        return {key: payload[key] for key in sorted(payload)}
