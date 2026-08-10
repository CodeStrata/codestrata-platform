"""Canonical Community Cloud API error model — no stack traces or secrets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.constants import (
    API_SURFACE,
    API_VERSION_V1,
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
)


# Stable public codes — do not invent free-form exception class names.
ERROR_NOT_FOUND = "not_found"
ERROR_METHOD_NOT_ALLOWED = "method_not_allowed"
ERROR_UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"
ERROR_MALFORMED_JSON = "malformed_json"
# Backward-compatible alias used by Slice 7.1 tests/docs.
ERROR_INVALID_JSON = ERROR_MALFORMED_JSON
ERROR_BODY_REQUIRED = "request_body_required"
ERROR_BODY_FORBIDDEN = "request_body_forbidden"
ERROR_INVALID_REQUEST_SCHEMA = "invalid_request_schema"
ERROR_UNSUPPORTED_JSON_SHAPE = "unsupported_json_shape"
ERROR_PAYLOAD_TOO_LARGE = "payload_too_large"
ERROR_PAYLOAD_TOO_DEEP = "payload_too_deep"
ERROR_PAYLOAD_ARRAY_LIMIT = "payload_array_limit"
ERROR_PAYLOAD_OBJECT_LIMIT = "payload_object_limit"
ERROR_PAYLOAD_STRING_LIMIT = "payload_string_limit"
ERROR_PAYLOAD_COMPLEXITY_LIMIT = "payload_complexity_limit"
ERROR_EVENT_IDENTITY_CONFLICT = "event_identity_conflict"
ERROR_EVENT_IDENTITY_UNAVAILABLE = "event_identity_unavailable"
ERROR_EVENT_IDENTITY_RECORD_FAILED = "event_identity_record_failed"
ERROR_UNSUPPORTED_TELEMETRY_SCHEMA = "unsupported_telemetry_schema"
ERROR_UNSUPPORTED_TELEMETRY_EVENT = "unsupported_telemetry_event"
ERROR_TELEMETRY_SINK_UNAVAILABLE = "telemetry_sink_unavailable"
ERROR_TELEMETRY_REJECTED = "telemetry_rejected"
ERROR_UNSUPPORTED_ASSESSMENT_METADATA_SCHEMA = "unsupported_assessment_metadata_schema"
ERROR_UNSUPPORTED_ASSESSMENT_HEAD = "unsupported_assessment_head"
ERROR_ASSESSMENT_METADATA_SINK_UNAVAILABLE = "assessment_metadata_sink_unavailable"
ERROR_ASSESSMENT_METADATA_REJECTED = "assessment_metadata_rejected"
ERROR_ASSESSMENT_METADATA_IDENTITY_UNAVAILABLE = (
    "assessment_metadata_identity_unavailable"
)
ERROR_ASSESSMENT_METADATA_RECORD_FAILED = "assessment_metadata_record_failed"
ERROR_UNSUPPORTED_CLI_EVENT_SCHEMA = "unsupported_cli_event_schema"
ERROR_UNSUPPORTED_CLI_OPERATION = "unsupported_cli_operation"
ERROR_UNSUPPORTED_CLI_LIFECYCLE = "unsupported_cli_lifecycle"
ERROR_UNSUPPORTED_CLI_RESULT = "unsupported_cli_result"
ERROR_CLI_EVENT_SINK_UNAVAILABLE = "cli_event_sink_unavailable"
ERROR_CLI_EVENT_REJECTED = "cli_event_rejected"
ERROR_CLI_EVENT_IDENTITY_UNAVAILABLE = "cli_event_identity_unavailable"
ERROR_CLI_EVENT_RECORD_FAILED = "cli_event_record_failed"
ERROR_UNSUPPORTED_EXTENSION_EVENT_SCHEMA = "unsupported_extension_event_schema"
ERROR_UNSUPPORTED_EXTENSION_CLIENT = "unsupported_extension_client"
ERROR_UNSUPPORTED_EXTENSION_EDITOR = "unsupported_extension_editor"
ERROR_UNSUPPORTED_EXTENSION_OPERATION = "unsupported_extension_operation"
ERROR_UNSUPPORTED_EXTENSION_LIFECYCLE = "unsupported_extension_lifecycle"
ERROR_UNSUPPORTED_EXTENSION_RESULT = "unsupported_extension_result"
ERROR_EXTENSION_EVENT_SINK_UNAVAILABLE = "extension_event_sink_unavailable"
ERROR_EXTENSION_EVENT_REJECTED = "extension_event_rejected"
ERROR_EXTENSION_EVENT_IDENTITY_UNAVAILABLE = "extension_event_identity_unavailable"
ERROR_EXTENSION_EVENT_RECORD_FAILED = "extension_event_record_failed"
ERROR_UNSUPPORTED_AI_USAGE_SCHEMA = "unsupported_ai_usage_schema"
ERROR_UNSUPPORTED_AI_CAPABILITY = "unsupported_ai_capability"
ERROR_UNSUPPORTED_AI_CLIENT = "unsupported_ai_client"
ERROR_UNSUPPORTED_AI_PROVIDER = "unsupported_ai_provider"
ERROR_UNSUPPORTED_AI_MODEL_FAMILY = "unsupported_ai_model_family"
ERROR_UNSUPPORTED_AI_OUTCOME = "unsupported_ai_outcome"
ERROR_INVALID_AI_USAGE_COMBINATION = "invalid_ai_usage_combination"
ERROR_AI_USAGE_SINK_UNAVAILABLE = "ai_usage_sink_unavailable"
ERROR_AI_USAGE_REJECTED = "ai_usage_rejected"
ERROR_AI_USAGE_IDENTITY_UNAVAILABLE = "ai_usage_identity_unavailable"
ERROR_AI_USAGE_RECORD_FAILED = "ai_usage_record_failed"
ERROR_RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
ERROR_RATE_LIMIT_UNAVAILABLE = "rate_limit_unavailable"
ERROR_INVALID_RATE_LIMIT_POLICY = "invalid_rate_limit_policy"
ERROR_AUTHENTICATION_REQUIRED = "authentication_required"
ERROR_INVALID_CLIENT_CREDENTIAL = "invalid_client_credential"
ERROR_INACTIVE_CLIENT_CREDENTIAL = "inactive_client_credential"
ERROR_AUTHENTICATION_UNAVAILABLE = "authentication_unavailable"
ERROR_CLIENT_NOT_AUTHORIZED = "client_not_authorized"
ERROR_INVALID_AUTHORIZATION_HEADER = "invalid_authorization_header"
ERROR_INTERNAL = "internal_error"
ERROR_VERSION_NOT_SUPPORTED = "api_version_not_supported"
ERROR_REPORT_STORE_UNAVAILABLE = "report_store_unavailable"
ERROR_EXPLICIT_PUBLISH_REQUIRED = "explicit_publish_required"
ERROR_PRIVATE_REPOSITORY_ACK_REQUIRED = "private_repository_ack_required"
ERROR_UPLOAD_INTENT_EXPIRED = "upload_intent_expired"
ERROR_ARTIFACT_MISSING = "artifact_missing"
ERROR_ARTIFACT_TOO_LARGE = "artifact_too_large"
ERROR_SANITIZER_REJECTED = "sanitizer_rejected"
ERROR_FORBIDDEN = "forbidden"


_SAFE_PUBLIC_MESSAGES: dict[str, str] = {
    ERROR_NOT_FOUND: "Endpoint not found.",
    ERROR_METHOD_NOT_ALLOWED: "HTTP method not allowed for this endpoint.",
    ERROR_UNSUPPORTED_MEDIA_TYPE: "Unsupported media type. Use application/json.",
    ERROR_MALFORMED_JSON: "Request body must be valid JSON.",
    ERROR_BODY_REQUIRED: "Request body is required.",
    ERROR_BODY_FORBIDDEN: "Request body is not permitted for this endpoint.",
    ERROR_INVALID_REQUEST_SCHEMA: "Request payload failed validation.",
    ERROR_UNSUPPORTED_JSON_SHAPE: "Request body must be a JSON object.",
    ERROR_PAYLOAD_TOO_LARGE: "Request payload exceeds the maximum allowed size.",
    ERROR_PAYLOAD_TOO_DEEP: "Request payload exceeds the maximum JSON nesting depth.",
    ERROR_PAYLOAD_ARRAY_LIMIT: "Request payload exceeds the maximum array length.",
    ERROR_PAYLOAD_OBJECT_LIMIT: "Request payload exceeds the maximum object property count.",
    ERROR_PAYLOAD_STRING_LIMIT: "Request payload exceeds the maximum string length.",
    ERROR_PAYLOAD_COMPLEXITY_LIMIT: "Request payload exceeds the maximum structural complexity.",
    ERROR_EVENT_IDENTITY_CONFLICT: (
        "Event identifier was previously used with different event content."
    ),
    ERROR_EVENT_IDENTITY_UNAVAILABLE: (
        "Telemetry event identity coordination is temporarily unavailable."
    ),
    ERROR_EVENT_IDENTITY_RECORD_FAILED: (
        "Telemetry event identity could not be recorded safely."
    ),
    ERROR_UNSUPPORTED_TELEMETRY_SCHEMA: "Unsupported telemetry schema version.",
    ERROR_UNSUPPORTED_TELEMETRY_EVENT: "Unsupported telemetry event type.",
    ERROR_TELEMETRY_SINK_UNAVAILABLE: "Telemetry ingestion is temporarily unavailable.",
    ERROR_TELEMETRY_REJECTED: "Telemetry event was rejected.",
    ERROR_UNSUPPORTED_ASSESSMENT_METADATA_SCHEMA: (
        "Unsupported assessment metadata schema version."
    ),
    ERROR_UNSUPPORTED_ASSESSMENT_HEAD: "Unsupported assessment head identifier.",
    ERROR_ASSESSMENT_METADATA_SINK_UNAVAILABLE: (
        "Assessment metadata ingestion is temporarily unavailable."
    ),
    ERROR_ASSESSMENT_METADATA_REJECTED: "Assessment metadata event was rejected.",
    ERROR_ASSESSMENT_METADATA_IDENTITY_UNAVAILABLE: (
        "Assessment metadata event identity coordination is temporarily unavailable."
    ),
    ERROR_ASSESSMENT_METADATA_RECORD_FAILED: (
        "Assessment metadata event identity could not be recorded safely."
    ),
    ERROR_UNSUPPORTED_CLI_EVENT_SCHEMA: "Unsupported CLI event schema version.",
    ERROR_UNSUPPORTED_CLI_OPERATION: "Unsupported CLI operation.",
    ERROR_UNSUPPORTED_CLI_LIFECYCLE: "Unsupported CLI event lifecycle.",
    ERROR_UNSUPPORTED_CLI_RESULT: "Unsupported CLI event result.",
    ERROR_CLI_EVENT_SINK_UNAVAILABLE: "CLI event ingestion is temporarily unavailable.",
    ERROR_CLI_EVENT_REJECTED: "CLI event was rejected.",
    ERROR_CLI_EVENT_IDENTITY_UNAVAILABLE: (
        "CLI event identity coordination is temporarily unavailable."
    ),
    ERROR_CLI_EVENT_RECORD_FAILED: "CLI event identity could not be recorded safely.",
    ERROR_UNSUPPORTED_EXTENSION_EVENT_SCHEMA: (
        "Unsupported extension event schema version."
    ),
    ERROR_UNSUPPORTED_EXTENSION_CLIENT: "Unsupported extension client.",
    ERROR_UNSUPPORTED_EXTENSION_EDITOR: "Unsupported extension editor.",
    ERROR_UNSUPPORTED_EXTENSION_OPERATION: "Unsupported extension operation.",
    ERROR_UNSUPPORTED_EXTENSION_LIFECYCLE: "Unsupported extension event lifecycle.",
    ERROR_UNSUPPORTED_EXTENSION_RESULT: "Unsupported extension event result.",
    ERROR_EXTENSION_EVENT_SINK_UNAVAILABLE: (
        "Extension event ingestion is temporarily unavailable."
    ),
    ERROR_EXTENSION_EVENT_REJECTED: "Extension event was rejected.",
    ERROR_EXTENSION_EVENT_IDENTITY_UNAVAILABLE: (
        "Extension event identity coordination is temporarily unavailable."
    ),
    ERROR_EXTENSION_EVENT_RECORD_FAILED: (
        "Extension event identity could not be recorded safely."
    ),
    ERROR_UNSUPPORTED_AI_USAGE_SCHEMA: "Unsupported AI usage schema version.",
    ERROR_UNSUPPORTED_AI_CAPABILITY: "Unsupported AI capability.",
    ERROR_UNSUPPORTED_AI_CLIENT: "Unsupported AI usage client.",
    ERROR_UNSUPPORTED_AI_PROVIDER: "Unsupported AI provider family.",
    ERROR_UNSUPPORTED_AI_MODEL_FAMILY: "Unsupported AI model family.",
    ERROR_UNSUPPORTED_AI_OUTCOME: "Unsupported AI usage outcome.",
    ERROR_INVALID_AI_USAGE_COMBINATION: "AI usage fields are not a valid combination.",
    ERROR_AI_USAGE_SINK_UNAVAILABLE: "AI usage ingestion is temporarily unavailable.",
    ERROR_AI_USAGE_REJECTED: "AI usage event was rejected.",
    ERROR_AI_USAGE_IDENTITY_UNAVAILABLE: (
        "AI usage event identity coordination is temporarily unavailable."
    ),
    ERROR_AI_USAGE_RECORD_FAILED: "AI usage event identity could not be recorded safely.",
    ERROR_RATE_LIMIT_EXCEEDED: "Request rate limit exceeded.",
    ERROR_RATE_LIMIT_UNAVAILABLE: "Request rate limiting is temporarily unavailable.",
    ERROR_INVALID_RATE_LIMIT_POLICY: "Rate-limit policy is invalid.",
    ERROR_AUTHENTICATION_REQUIRED: "Authentication is required.",
    ERROR_INVALID_CLIENT_CREDENTIAL: "Client credential is invalid.",
    ERROR_INACTIVE_CLIENT_CREDENTIAL: "Client credential is invalid.",
    ERROR_AUTHENTICATION_UNAVAILABLE: "Client authentication is temporarily unavailable.",
    ERROR_CLIENT_NOT_AUTHORIZED: "Client is not authorized for this API route.",
    ERROR_INVALID_AUTHORIZATION_HEADER: "Authorization header is invalid.",
    # Insights shared-password auth (must not remap to internal_error).
    "invalid_credentials": "Invalid password",
    "session_expired": "Session expired",
    "invalid_session": "Invalid session",
    "authorization_denied": "Access denied",
    "auth_service_unavailable": "Authentication unavailable",
    "invalid_origin": "Invalid request origin",
    "rate_limited": "Too many requests",
    "internal_auth_error": "Authentication error",
    ERROR_INTERNAL: "An unexpected error occurred.",
    ERROR_VERSION_NOT_SUPPORTED: "API version is not supported.",
    ERROR_REPORT_STORE_UNAVAILABLE: "Report publishing is temporarily unavailable.",
    ERROR_EXPLICIT_PUBLISH_REQUIRED: "Explicit public-publish confirmation is required.",
    ERROR_PRIVATE_REPOSITORY_ACK_REQUIRED: (
        "Publishing creates a publicly accessible report. Anyone with the link can view it."
    ),
    ERROR_UPLOAD_INTENT_EXPIRED: "Upload intent expired.",
    ERROR_ARTIFACT_MISSING: "Required report artifact is missing from staging.",
    ERROR_ARTIFACT_TOO_LARGE: "Report artifact exceeds the maximum allowed size.",
    ERROR_SANITIZER_REJECTED: "Report content failed publication sanitizer checks.",
    ERROR_FORBIDDEN: "Client is not authorized for this report operation.",
}

ErrorDetails = Mapping[str, Any] | Sequence[Mapping[str, Any]]


def _stabilize_details(details: ErrorDetails | None) -> ErrorDetails | None:
    if details is None:
        return None
    if isinstance(details, Mapping):
        return dict(sorted(details.items(), key=lambda item: str(item[0])))
    stabilized: list[dict[str, Any]] = []
    for item in details:
        stabilized.append({str(key): item[key] for key in sorted(item, key=str)})
    return tuple(
        sorted(
            stabilized,
            key=lambda row: (
                str(row.get("field", "")),
                str(row.get("code", "")),
                str(row.get("message", "")),
            ),
        )
    )


@dataclass(frozen=True, slots=True)
class ApiError:
    """Deterministic public error envelope body (without HTTP status)."""

    code: str
    message: str
    api_version: str = API_VERSION_V1
    details: ErrorDetails | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        code = (self.code or "").strip()
        if not code:
            raise ValueError("error code is required")
        message = (self.message or "").strip()
        if not message:
            raise ValueError("error message is required")
        compact = " ".join(message.split())
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "message", compact)
        object.__setattr__(self, "details", _stabilize_details(self.details))

    @classmethod
    def of(
        cls,
        code: str,
        *,
        api_version: str = API_VERSION_V1,
        details: ErrorDetails | None = None,
        request_id: str | None = None,
        message: str | None = None,
    ) -> ApiError:
        """Build an error using the allowlisted public message for ``code``."""

        resolved_code = code if code in _SAFE_PUBLIC_MESSAGES else ERROR_INTERNAL
        public_message = _SAFE_PUBLIC_MESSAGES[resolved_code]
        if message is not None and message.strip() == public_message:
            pass
        return cls(
            code=resolved_code,
            message=public_message,
            api_version=api_version,
            details=details,
            request_id=(request_id or "").strip() or None,
        )

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "api_version": self.api_version,
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            if isinstance(self.details, Mapping):
                payload["details"] = dict(self.details)
            else:
                payload["details"] = [dict(item) for item in self.details]
        if self.request_id:
            payload["request_id"] = self.request_id
        return {key: payload[key] for key in sorted(payload)}


@dataclass(frozen=True, slots=True)
class ApiErrorResponse:
    """Top-level error response document."""

    error: ApiError
    meta: Mapping[str, Any]

    @classmethod
    def build(
        cls,
        code: str,
        *,
        http_status: int,
        api_version: str = API_VERSION_V1,
        details: ErrorDetails | None = None,
        request_id: str | None = None,
        message: str | None = None,
        meta_extra: Mapping[str, Any] | None = None,
    ) -> ApiErrorResponse:
        error = ApiError.of(
            code,
            api_version=api_version,
            details=details,
            request_id=request_id,
            message=message,
        )
        meta: dict[str, Any] = {
            "api_schema_version": COMMUNITY_CLOUD_API_SCHEMA_VERSION,
            "api_surface": API_SURFACE,
            "api_version": api_version,
            "http_status": int(http_status),
        }
        if meta_extra:
            for key, value in meta_extra.items():
                meta[str(key)] = value
        return cls(error=error, meta={key: meta[key] for key in sorted(meta)})

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "error": self.error.to_stable_dict(),
            "meta": dict(sorted(self.meta.items(), key=lambda item: str(item[0]))),
        }
