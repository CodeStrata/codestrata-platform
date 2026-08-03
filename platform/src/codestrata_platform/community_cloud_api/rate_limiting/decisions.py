"""Rate-limit decision model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DECISION_ALLOWED = "allowed"
DECISION_LIMITED = "limited"
DECISION_UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """Outcome of rate-limit evaluation — no raw IP or store internals."""

    status: str
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int | None
    reset_after_seconds: int
    safe_scope_reference: str
    policy_id: str
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {
            DECISION_ALLOWED,
            DECISION_LIMITED,
            DECISION_UNAVAILABLE,
        }:
            raise ValueError(f"invalid decision status: {self.status}")
        if self.remaining < 0:
            raise ValueError("remaining must be >= 0")
        if self.limit < 0:
            raise ValueError("limit must be >= 0")
        if self.reset_after_seconds < 0:
            raise ValueError("reset_after_seconds must be >= 0")
        if self.status == DECISION_LIMITED:
            if self.allowed:
                raise ValueError("limited decisions must not be allowed")
            if self.retry_after_seconds is None or int(self.retry_after_seconds) < 1:
                raise ValueError("limited decisions require positive retry_after_seconds")
        elif self.retry_after_seconds is not None:
            raise ValueError("retry_after_seconds only permitted when limited")
        if self.status == DECISION_ALLOWED and not self.allowed:
            raise ValueError("allowed status requires allowed=True")
        if self.status == DECISION_UNAVAILABLE and self.allowed:
            raise ValueError("unavailable decisions must not be allowed")
        object.__setattr__(self, "remaining", max(0, int(self.remaining)))
        object.__setattr__(self, "limit", int(self.limit))
        object.__setattr__(self, "reset_after_seconds", int(self.reset_after_seconds))
        if self.retry_after_seconds is not None:
            object.__setattr__(self, "retry_after_seconds", int(self.retry_after_seconds))
        object.__setattr__(
            self,
            "limitations",
            tuple(sorted(str(item) for item in self.limitations)),
        )

    @classmethod
    def allowed_decision(
        cls,
        *,
        limit: int,
        remaining: int,
        reset_after_seconds: int,
        safe_scope_reference: str,
        policy_id: str,
        limitations: tuple[str, ...] = (),
    ) -> RateLimitDecision:
        return cls(
            status=DECISION_ALLOWED,
            allowed=True,
            limit=limit,
            remaining=max(0, remaining),
            retry_after_seconds=None,
            reset_after_seconds=reset_after_seconds,
            safe_scope_reference=safe_scope_reference,
            policy_id=policy_id,
            limitations=limitations,
        )

    @classmethod
    def limited_decision(
        cls,
        *,
        limit: int,
        remaining: int,
        retry_after_seconds: int,
        reset_after_seconds: int,
        safe_scope_reference: str,
        policy_id: str,
        limitations: tuple[str, ...] = (),
    ) -> RateLimitDecision:
        return cls(
            status=DECISION_LIMITED,
            allowed=False,
            limit=limit,
            remaining=max(0, remaining),
            retry_after_seconds=max(1, int(retry_after_seconds)),
            reset_after_seconds=reset_after_seconds,
            safe_scope_reference=safe_scope_reference,
            policy_id=policy_id,
            limitations=limitations,
        )

    @classmethod
    def unavailable_decision(
        cls,
        *,
        limit: int,
        safe_scope_reference: str,
        policy_id: str,
        limitations: tuple[str, ...] = (),
    ) -> RateLimitDecision:
        return cls(
            status=DECISION_UNAVAILABLE,
            allowed=False,
            limit=limit,
            remaining=0,
            retry_after_seconds=None,
            reset_after_seconds=0,
            safe_scope_reference=safe_scope_reference,
            policy_id=policy_id,
            limitations=limitations,
        )

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "allowed": self.allowed,
            "limit": self.limit,
            "limitations": list(self.limitations),
            "policy_id": self.policy_id,
            "remaining": self.remaining,
            "reset_after_seconds": self.reset_after_seconds,
            "safe_scope_reference": self.safe_scope_reference,
            "status": self.status,
        }
        if self.retry_after_seconds is not None:
            payload["retry_after_seconds"] = self.retry_after_seconds
        return {key: payload[key] for key in sorted(payload)}
