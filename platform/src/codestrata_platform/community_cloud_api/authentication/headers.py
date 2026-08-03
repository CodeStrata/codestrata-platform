"""Authorization header parsing for Community client credentials."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.community_cloud_api.authentication.credentials import (
    CommunityClientCredential,
    parse_credential_token,
)
from codestrata_platform.community_cloud_api.authentication.models import (
    ACCEPTED_SCHEME_BEARER,
    CommunityAuthenticationPolicy,
)

HEADER_AUTHORIZATION = "Authorization"


@dataclass(frozen=True, slots=True)
class AuthorizationParseResult:
    status: str  # ok | missing | invalid
    credential: CommunityClientCredential | None = None
    reason: str | None = None


def parse_authorization_header(
    *,
    authorization_header: str | None = None,
    authorization_headers: list[str] | None = None,
    policy: CommunityAuthenticationPolicy,
) -> AuthorizationParseResult:
    """Parse a single Authorization: Bearer <token> header."""

    values: list[str] = []
    if authorization_headers is not None:
        values = [item for item in authorization_headers if item is not None]
    elif authorization_header is not None:
        values = [authorization_header]

    if not values:
        return AuthorizationParseResult(status="missing", reason="missing_authorization")
    if len(values) > 1:
        return AuthorizationParseResult(
            status="invalid", reason="duplicate_authorization_header"
        )

    raw = values[0]
    if raw is None or not str(raw).strip():
        return AuthorizationParseResult(status="missing", reason="empty_authorization")

    text = str(raw).strip()
    if "," in text:
        return AuthorizationParseResult(
            status="invalid", reason="multiple_credentials"
        )

    parts = text.split(None, 1)
    if len(parts) != 2:
        return AuthorizationParseResult(status="invalid", reason="malformed_authorization")

    scheme, token = parts[0], parts[1]
    if scheme.lower() != ACCEPTED_SCHEME_BEARER.lower():
        return AuthorizationParseResult(status="invalid", reason="unsupported_scheme")
    if not token or any(ch.isspace() for ch in token):
        return AuthorizationParseResult(status="invalid", reason="empty_token")

    credential = parse_credential_token(token, policy=policy)
    if credential is None:
        return AuthorizationParseResult(status="invalid", reason="invalid_token_format")
    return AuthorizationParseResult(status="ok", credential=credential)
