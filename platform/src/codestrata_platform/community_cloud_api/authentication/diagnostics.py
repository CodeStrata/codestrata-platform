"""Internal authentication diagnostics — never returned in API responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AuthenticationDiagnostics:
    route_id: str
    decision_status: str
    verifier_status: str
    safe_client_reference: str | None
    client_type: str | None
    authentication_policy_id: str
    rate_limit_scope_status: str
    limitations: tuple[str, ...] = ()

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "authentication_policy_id": self.authentication_policy_id,
            "decision_status": self.decision_status,
            "limitations": list(self.limitations),
            "rate_limit_scope_status": self.rate_limit_scope_status,
            "route_id": self.route_id,
            "verifier_status": self.verifier_status,
        }
        if self.client_type is not None:
            payload["client_type"] = self.client_type
        if self.safe_client_reference is not None:
            payload["safe_client_reference"] = self.safe_client_reference
        return {key: payload[key] for key in sorted(payload)}
