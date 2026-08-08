"""Shared request/response foundation models (no business payloads)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from codestrata_platform.community_cloud_api.constants import (
    API_SURFACE,
    API_VERSION_V1,
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
)


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Per-request foundation context — no raw credentials or tenant state."""

    api_version: str
    method: str
    path: str
    request_id: str | None = None
    content_type: str | None = None
    accepted_json: bool = True
    # Set only after fail-closed schema validation succeeds.
    validated_request: Any | None = None
    # Safe principal only — never raw token / fingerprint.
    authenticated_client: Any | None = None
    # Transport headers for Insights session cookies / CSRF (Slice 15.9).
    cookie_header: str | None = None
    origin_header: str | None = None
    referer_header: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "api_version", (self.api_version or "").strip())
        object.__setattr__(self, "method", (self.method or "").strip().upper())
        object.__setattr__(self, "path", (self.path or "").strip() or "/")
        rid = (self.request_id or "").strip() or None
        object.__setattr__(self, "request_id", rid)
        ctype = (self.content_type or "").strip() or None
        object.__setattr__(self, "content_type", ctype)
        cookie = (self.cookie_header or "").strip() or None
        object.__setattr__(self, "cookie_header", cookie)
        origin = (self.origin_header or "").strip() or None
        object.__setattr__(self, "origin_header", origin)
        referer = (self.referer_header or "").strip() or None
        object.__setattr__(self, "referer_header", referer)

    def with_validated_request(self, model: Any) -> RequestContext:
        return RequestContext(
            api_version=self.api_version,
            method=self.method,
            path=self.path,
            request_id=self.request_id,
            content_type=self.content_type,
            accepted_json=self.accepted_json,
            validated_request=model,
            authenticated_client=self.authenticated_client,
            cookie_header=self.cookie_header,
            origin_header=self.origin_header,
            referer_header=self.referer_header,
        )

    def with_authenticated_client(self, principal: Any | None) -> RequestContext:
        return RequestContext(
            api_version=self.api_version,
            method=self.method,
            path=self.path,
            request_id=self.request_id,
            content_type=self.content_type,
            accepted_json=self.accepted_json,
            validated_request=self.validated_request,
            authenticated_client=principal,
            cookie_header=self.cookie_header,
            origin_header=self.origin_header,
            referer_header=self.referer_header,
        )

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "accepted_json": self.accepted_json,
            "api_version": self.api_version,
            "method": self.method,
            "path": self.path,
        }
        if self.content_type is not None:
            payload["content_type"] = self.content_type
        if self.request_id is not None:
            payload["request_id"] = self.request_id
        if self.authenticated_client is not None and hasattr(
            self.authenticated_client, "to_stable_dict"
        ):
            payload["authenticated_client"] = self.authenticated_client.to_stable_dict()
        return {key: payload[key] for key in sorted(payload)}


@dataclass(frozen=True, slots=True)
class ResponseMetadata:
    """Stable response metadata attached to successful foundation responses."""

    api_version: str = API_VERSION_V1
    api_surface: str = API_SURFACE
    api_schema_version: str = COMMUNITY_CLOUD_API_SCHEMA_VERSION
    request_id: str | None = None

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "api_schema_version": self.api_schema_version,
            "api_surface": self.api_surface,
            "api_version": self.api_version,
        }
        if self.request_id:
            payload["request_id"] = self.request_id
        return {key: payload[key] for key in sorted(payload)}


@dataclass(frozen=True, slots=True)
class ApiDiagnostics:
    """Factual foundation diagnostics — no marketing conclusions."""

    registered_route_count: int = 0
    supported_version_count: int = 0
    api_version: str = API_VERSION_V1
    api_surface: str = API_SURFACE
    limitations: tuple[str, ...] = (
        "slice_7_13_client_authentication",
        "six_production_routes",
        "no_production_event_store",
        "no_exactly_once_guarantee",
        "client_credential_auth_only",
        "no_user_or_organization_identity",
        "process_local_rate_limiting_only",
        "no_distributed_rate_limit_store",
        "no_production_credential_store",
        "no_persistence",
        "no_log_shipping",
        "health_is_process_availability_only",
        "no_cli_emitter_wiring",
        "no_extension_emitter_wiring",
        "no_ai_usage_emitter_wiring",
    )

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "api_surface": self.api_surface,
            "api_version": self.api_version,
            "limitations": list(self.limitations),
            "registered_route_count": self.registered_route_count,
            "supported_version_count": self.supported_version_count,
        }


@dataclass(frozen=True, slots=True)
class ApiSuccessEnvelope:
    """Generic success envelope for future endpoints (unused in Slice 7.1)."""

    data: Mapping[str, Any] = field(default_factory=dict)
    meta: ResponseMetadata = field(default_factory=ResponseMetadata)

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "data": dict(sorted((str(k), v) for k, v in self.data.items())),
            "meta": self.meta.to_stable_dict(),
        }
