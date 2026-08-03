"""Internal rate-limit diagnostics — never returned in API responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RateLimitDiagnostics:
    """Safe diagnostic snapshot for tests and local inspection."""

    route_id: str
    decision_status: str
    limit: int
    remaining: int
    retry_after_seconds: int | None
    safe_scope_reference: str
    policy_id: str
    store_status: str
    limitations: tuple[str, ...] = ()

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "decision_status": self.decision_status,
            "limit": self.limit,
            "limitations": list(self.limitations),
            "policy_id": self.policy_id,
            "remaining": self.remaining,
            "route_id": self.route_id,
            "safe_scope_reference": self.safe_scope_reference,
            "store_status": self.store_status,
        }
        if self.retry_after_seconds is not None:
            payload["retry_after_seconds"] = self.retry_after_seconds
        return {key: payload[key] for key in sorted(payload)}
