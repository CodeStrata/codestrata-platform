"""Event-identity policy and core models (Slice 7.6)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


COMMUNITY_EVENT_IDENTITY_POLICY_ID = "community-event-identity-policy"
COMMUNITY_EVENT_IDENTITY_POLICY_VERSION = "1.0"
COMMUNITY_EVENT_IDENTITY_POLICY_URN = (
    f"{COMMUNITY_EVENT_IDENTITY_POLICY_ID}:{COMMUNITY_EVENT_IDENTITY_POLICY_VERSION}"
)
FINGERPRINT_POLICY_VERSION = "1.0"

DEFAULT_FINGERPRINT_EXCLUDED_FIELDS: tuple[str, ...] = (
    "request_id",
    "retry_count",
    "received_at",
    "transport_metadata",
    "server_metadata",
)

DEFAULT_SCOPE_COMPONENTS: tuple[str, ...] = (
    "api_version",
    "client_type",
    "installation_id",
    "event_type",
    "event_id",
)


class RetryStatus(str, Enum):
    FIRST_SEEN = "first_seen"
    EXACT_RETRY = "exact_retry"
    CONFLICTING_RETRY = "conflicting_retry"
    UNAVAILABLE = "unavailable"


class IdempotencyOutcome(str, Enum):
    """Future endpoint outcomes — not bound to production routes in 7.6."""

    ACCEPTED = "accepted"
    ALREADY_ACCEPTED = "already_accepted"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class CommunityEventIdentityPolicy:
    """Deterministic event-identity / retry-safety policy."""

    policy_id: str = COMMUNITY_EVENT_IDENTITY_POLICY_ID
    policy_version: str = COMMUNITY_EVENT_IDENTITY_POLICY_VERSION
    event_id_min_length: int = 8
    event_id_max_length: int = 128
    allowed_character_policy: str = "A-Za-z0-9._:-"
    scope_components: tuple[str, ...] = DEFAULT_SCOPE_COMPONENTS
    fingerprint_policy_version: str = FINGERPRINT_POLICY_VERSION
    fingerprint_excluded_fields: tuple[str, ...] = DEFAULT_FINGERPRINT_EXCLUDED_FIELDS
    conflict_behavior: str = "reject"
    safe_log_identifier_length: int = 12
    limitations: tuple[str, ...] = (
        "no_production_deduplication_store",
        "installation_id_optional_future_scope",
        "hashes_are_not_encryption",
        "no_exactly_once_guarantee",
    )

    def __post_init__(self) -> None:
        if self.policy_id != COMMUNITY_EVENT_IDENTITY_POLICY_ID:
            raise ValueError("unsupported event identity policy id")
        if self.policy_version != COMMUNITY_EVENT_IDENTITY_POLICY_VERSION:
            raise ValueError("unsupported event identity policy version")
        if self.event_id_min_length < 8 or self.event_id_max_length > 128:
            raise ValueError("event_id length bounds out of range")
        if self.event_id_min_length > self.event_id_max_length:
            raise ValueError("event_id_min_length must be <= event_id_max_length")
        if self.safe_log_identifier_length < 8 or self.safe_log_identifier_length > 32:
            raise ValueError("safe_log_identifier_length out of range")
        if self.conflict_behavior != "reject":
            raise ValueError("only reject conflict behavior is supported in policy 1.0")
        for field in self.fingerprint_excluded_fields:
            if not field or any(ch.isspace() for ch in field):
                raise ValueError("invalid fingerprint excluded field")
            if field in {"event_id", "event_type", "client_type"}:
                raise ValueError(f"cannot exclude identity field from fingerprint: {field}")
        object.__setattr__(
            self,
            "scope_components",
            tuple(sorted(self.scope_components)),
        )
        object.__setattr__(
            self,
            "fingerprint_excluded_fields",
            tuple(sorted(set(self.fingerprint_excluded_fields))),
        )
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    @classmethod
    def default(cls) -> CommunityEventIdentityPolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "allowed_character_policy": self.allowed_character_policy,
            "conflict_behavior": self.conflict_behavior,
            "event_id_max_length": self.event_id_max_length,
            "event_id_min_length": self.event_id_min_length,
            "fingerprint_excluded_fields": list(self.fingerprint_excluded_fields),
            "fingerprint_policy_version": self.fingerprint_policy_version,
            "limitations": list(self.limitations),
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "safe_log_identifier_length": self.safe_log_identifier_length,
            "scope_components": list(self.scope_components),
        }


@dataclass(frozen=True, slots=True)
class EventIdentityScope:
    """Scoped logical event identity — not request_id and not payload content."""

    api_version: str
    client_type: str
    event_type: str
    event_id: str
    installation_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "api_version", (self.api_version or "").strip())
        object.__setattr__(self, "client_type", (self.client_type or "").strip())
        object.__setattr__(self, "event_type", (self.event_type or "").strip())
        object.__setattr__(self, "event_id", (self.event_id or "").strip())
        install = (self.installation_id or "").strip() or None
        object.__setattr__(self, "installation_id", install)
        if not self.api_version or not self.client_type or not self.event_type or not self.event_id:
            raise ValueError("event identity scope requires api_version, client_type, event_type, event_id")

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "api_version": self.api_version,
            "client_type": self.client_type,
            "event_id": self.event_id,
            "event_type": self.event_type,
        }
        if self.installation_id is not None:
            payload["installation_id"] = self.installation_id
        return {key: payload[key] for key in sorted(payload)}


@dataclass(frozen=True, slots=True)
class StoredEventIdentity:
    """Minimum fields for future deduplication — never stores payloads."""

    event_key: str
    payload_fingerprint: str
    event_type: str
    client_type: str
    identity_policy_version: str

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "client_type": self.client_type,
            "event_key": self.event_key,
            "event_type": self.event_type,
            "identity_policy_version": self.identity_policy_version,
            "payload_fingerprint": self.payload_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class RetryDecision:
    """Deterministic retry classification for a scoped event identity."""

    status: RetryStatus
    event_key: str
    payload_fingerprint: str
    reason: str
    safe_event_reference: str
    existing_payload_fingerprint: str | None = None
    limitations: tuple[str, ...] = ()

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "event_key": self.event_key,
            "limitations": list(self.limitations),
            "payload_fingerprint": self.payload_fingerprint,
            "reason": self.reason,
            "safe_event_reference": self.safe_event_reference,
            "status": self.status.value,
        }
        if self.existing_payload_fingerprint is not None:
            payload["existing_payload_fingerprint"] = self.existing_payload_fingerprint
        return {key: payload[key] for key in sorted(payload)}

    def future_outcome(self) -> IdempotencyOutcome | None:
        if self.status is RetryStatus.FIRST_SEEN:
            return IdempotencyOutcome.ACCEPTED
        if self.status is RetryStatus.EXACT_RETRY:
            return IdempotencyOutcome.ALREADY_ACCEPTED
        if self.status is RetryStatus.CONFLICTING_RETRY:
            return IdempotencyOutcome.CONFLICT
        return None
