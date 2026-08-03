"""HTTP responses for authentication outcomes."""

from __future__ import annotations

from starlette.responses import Response

from codestrata_platform.community_cloud_api.authentication.decisions import (
    DECISION_MISSING,
    DECISION_SCOPE_MISMATCH,
    DECISION_UNAVAILABLE,
    AuthenticationDecision,
)
from codestrata_platform.community_cloud_api.authentication.models import (
    CommunityAuthenticationPolicy,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_AUTHENTICATION_REQUIRED,
    ERROR_AUTHENTICATION_UNAVAILABLE,
    ERROR_CLIENT_NOT_AUTHORIZED,
    ERROR_INVALID_AUTHORIZATION_HEADER,
    ERROR_INVALID_CLIENT_CREDENTIAL,
    ApiErrorResponse,
)
from codestrata_platform.community_cloud_api.serialization import (
    build_error_response,
    build_json_response,
)

HEADER_WWW_AUTHENTICATE = "WWW-Authenticate"
WWW_AUTHENTICATE_BEARER = "Bearer"


def build_authentication_error_response(
    decision: AuthenticationDecision,
    *,
    api_version: str,
    request_id: str | None,
    policy: CommunityAuthenticationPolicy,
) -> Response:
    if decision.status == DECISION_UNAVAILABLE:
        return build_error_response(
            ERROR_AUTHENTICATION_UNAVAILABLE,
            http_status=503,
            api_version=api_version,
            request_id=request_id,
        )
    if decision.status == DECISION_SCOPE_MISMATCH:
        return build_error_response(
            ERROR_CLIENT_NOT_AUTHORIZED,
            http_status=403,
            api_version=api_version,
            request_id=request_id,
        )

    if decision.status == DECISION_MISSING:
        code = ERROR_AUTHENTICATION_REQUIRED
    elif decision.reason in {
        "malformed_authorization",
        "unsupported_scheme",
        "duplicate_authorization_header",
        "multiple_credentials",
        "empty_token",
        "invalid_token_format",
    }:
        code = ERROR_INVALID_AUTHORIZATION_HEADER
    else:
        code = ERROR_INVALID_CLIENT_CREDENTIAL

    envelope = ApiErrorResponse.build(
        code,
        http_status=401,
        api_version=api_version,
        request_id=request_id,
    )
    extra = {}
    if policy.include_www_authenticate_on_401:
        extra[HEADER_WWW_AUTHENTICATE] = WWW_AUTHENTICATE_BEARER
    return build_json_response(
        envelope,
        status_code=401,
        api_version=api_version,
        request_id=request_id,
        extra_headers=extra,
    )


def build_client_not_authorized_response(
    *,
    api_version: str,
    request_id: str | None,
) -> Response:
    return build_error_response(
        ERROR_CLIENT_NOT_AUTHORIZED,
        http_status=403,
        api_version=api_version,
        request_id=request_id,
    )


def decision_error_code(decision: AuthenticationDecision) -> str:
    if decision.status == DECISION_UNAVAILABLE:
        return ERROR_AUTHENTICATION_UNAVAILABLE
    if decision.status == DECISION_SCOPE_MISMATCH:
        return ERROR_CLIENT_NOT_AUTHORIZED
    if decision.status == DECISION_MISSING:
        return ERROR_AUTHENTICATION_REQUIRED
    if decision.reason in {
        "malformed_authorization",
        "unsupported_scheme",
        "duplicate_authorization_header",
        "multiple_credentials",
        "empty_token",
        "invalid_token_format",
    }:
        return ERROR_INVALID_AUTHORIZATION_HEADER
    return ERROR_INVALID_CLIENT_CREDENTIAL
