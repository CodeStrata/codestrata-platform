"""Payload limit policy models and results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PAYLOAD_LIMIT_POLICY_ID = "payload-limit-policy"
PAYLOAD_LIMIT_POLICY_VERSION = "1.0"
PAYLOAD_LIMIT_POLICY_URN = f"{PAYLOAD_LIMIT_POLICY_ID}:{PAYLOAD_LIMIT_POLICY_VERSION}"


@dataclass(frozen=True, slots=True)
class PayloadLimitPolicy:
    """Deterministic transport payload limits (no endpoint overrides in 7.4)."""

    policy_version: str = PAYLOAD_LIMIT_POLICY_URN
    max_request_bytes: int = 65_536
    max_json_depth: int = 8
    max_array_length: int = 100
    max_object_properties: int = 100
    max_string_length: int = 4_096
    max_traversal_count: int = 10_000

    def __post_init__(self) -> None:
        if self.policy_version != PAYLOAD_LIMIT_POLICY_URN:
            raise ValueError("unsupported payload limit policy version")
        for name in (
            "max_request_bytes",
            "max_json_depth",
            "max_array_length",
            "max_object_properties",
            "max_string_length",
            "max_traversal_count",
        ):
            value = int(getattr(self, name))
            if value < 1:
                raise ValueError(f"{name} must be >= 1")
            object.__setattr__(self, name, value)

    @classmethod
    def default(cls) -> PayloadLimitPolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "max_array_length": self.max_array_length,
            "max_json_depth": self.max_json_depth,
            "max_object_properties": self.max_object_properties,
            "max_request_bytes": self.max_request_bytes,
            "max_string_length": self.max_string_length,
            "max_traversal_count": self.max_traversal_count,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True, slots=True)
class PayloadLimitResult:
    """Outcome of payload-size enforcement — never includes payload fragments."""

    ok: bool
    error_code: str | None = None
    http_status: int | None = None
    limit_name: str | None = None
    policy_version: str = PAYLOAD_LIMIT_POLICY_URN

    @classmethod
    def success(cls, *, policy_version: str = PAYLOAD_LIMIT_POLICY_URN) -> PayloadLimitResult:
        return cls(ok=True, policy_version=policy_version)

    @classmethod
    def rejected(
        cls,
        *,
        error_code: str,
        http_status: int,
        limit_name: str,
        policy_version: str = PAYLOAD_LIMIT_POLICY_URN,
    ) -> PayloadLimitResult:
        return cls(
            ok=False,
            error_code=error_code,
            http_status=http_status,
            limit_name=limit_name,
            policy_version=policy_version,
        )

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": self.ok,
            "policy_version": self.policy_version,
        }
        if self.error_code is not None:
            payload["error_code"] = self.error_code
        if self.http_status is not None:
            payload["http_status"] = self.http_status
        if self.limit_name is not None:
            payload["limit_name"] = self.limit_name
        return {key: payload[key] for key in sorted(payload)}
