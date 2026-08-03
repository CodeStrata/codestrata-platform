"""Authentication decision model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.authentication.models import (
    AuthenticatedCommunityClient,
)

DECISION_AUTHENTICATED = "authenticated"
DECISION_MISSING = "missing"
DECISION_INVALID = "invalid"
DECISION_INACTIVE = "inactive"
DECISION_SCOPE_MISMATCH = "scope_mismatch"
DECISION_UNAVAILABLE = "unavailable"
DECISION_DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class AuthenticationDecision:
    """Auth outcome — no raw token, fingerprint, or client_id in public dumps."""

    status: str
    authenticated: bool
    principal: AuthenticatedCommunityClient | None
    safe_client_reference: str | None
    reason: str
    policy_id: str
    verifier_status: str
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {
            DECISION_AUTHENTICATED,
            DECISION_MISSING,
            DECISION_INVALID,
            DECISION_INACTIVE,
            DECISION_SCOPE_MISMATCH,
            DECISION_UNAVAILABLE,
            DECISION_DISABLED,
        }:
            raise ValueError(f"invalid authentication status: {self.status}")
        if self.authenticated and self.principal is None:
            raise ValueError("authenticated decision requires principal")
        if not self.authenticated and self.principal is not None:
            raise ValueError("failed decisions must not carry principal")
        object.__setattr__(
            self,
            "limitations",
            tuple(sorted(str(item) for item in self.limitations)),
        )

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "authenticated": self.authenticated,
            "limitations": list(self.limitations),
            "policy_id": self.policy_id,
            "reason": self.reason,
            "status": self.status,
            "verifier_status": self.verifier_status,
        }
        if self.safe_client_reference is not None:
            payload["safe_client_reference"] = self.safe_client_reference
        if self.principal is not None:
            payload["client_type"] = self.principal.client_type
        return {key: payload[key] for key in sorted(payload)}
