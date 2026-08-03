"""Typed health response model for Community Cloud API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from codestrata_platform import __version__ as PLATFORM_VERSION
from codestrata_platform.community_cloud_api.constants import (
    API_VERSION_V1,
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
)

HEALTH_STATUS_OK: Literal["ok"] = "ok"
HEALTH_SERVICE_NAME = "codestrata-community-cloud-api"


@dataclass(frozen=True, slots=True)
class CommunityHealthResponse:
    """Process/API availability payload — no infrastructure or dependency state."""

    status: str = HEALTH_STATUS_OK
    service: str = HEALTH_SERVICE_NAME
    api_version: str = API_VERSION_V1
    schema_version: str = COMMUNITY_CLOUD_API_SCHEMA_VERSION
    application_version: str | None = PLATFORM_VERSION

    def __post_init__(self) -> None:
        if self.status != HEALTH_STATUS_OK:
            raise ValueError("health status must be 'ok' in Slice 7.2")
        if not (self.service or "").strip():
            raise ValueError("service name is required")
        object.__setattr__(self, "service", self.service.strip())
        object.__setattr__(self, "api_version", (self.api_version or "").strip())
        object.__setattr__(self, "schema_version", (self.schema_version or "").strip())
        app_ver = (self.application_version or "").strip() or None
        object.__setattr__(self, "application_version", app_ver)

    @classmethod
    def build(cls) -> CommunityHealthResponse:
        """Build the canonical healthy response from version constants only."""

        return cls(
            status=HEALTH_STATUS_OK,
            service=HEALTH_SERVICE_NAME,
            api_version=API_VERSION_V1,
            schema_version=COMMUNITY_CLOUD_API_SCHEMA_VERSION,
            application_version=PLATFORM_VERSION,
        )

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "api_version": self.api_version,
            "schema_version": self.schema_version,
            "service": self.service,
            "status": self.status,
        }
        if self.application_version is not None:
            payload["application_version"] = self.application_version
        return {key: payload[key] for key in sorted(payload)}
