"""Safe payload-limit diagnostics (no payload fragments)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.payload_limits.models import (
    PayloadLimitResult,
)


@dataclass(frozen=True, slots=True)
class PayloadLimitDiagnostic:
    """Internal diagnostic for future structured logging — values never included."""

    route_name: str
    error_code: str
    limit_name: str
    policy_version: str
    request_bytes: int | None = None

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error_code": self.error_code,
            "limit_name": self.limit_name,
            "policy_version": self.policy_version,
            "route_name": self.route_name,
        }
        if self.request_bytes is not None:
            # Count only — never offsets or content.
            payload["request_bytes"] = int(self.request_bytes)
        return {key: payload[key] for key in sorted(payload)}


def build_payload_limit_diagnostic(
    *,
    route_name: str,
    result: PayloadLimitResult,
    request_bytes: int | None = None,
) -> PayloadLimitDiagnostic | None:
    if result.ok or not result.error_code or not result.limit_name:
        return None
    return PayloadLimitDiagnostic(
        route_name=route_name,
        error_code=result.error_code,
        limit_name=result.limit_name,
        policy_version=result.policy_version,
        request_bytes=request_bytes,
    )
