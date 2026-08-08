"""Signed session tokens — HMAC-SHA256; claims stay minimal."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Callable

from codestrata_platform.community_cloud_api.insights_auth.errors import (
    ERROR_INVALID_SESSION,
    ERROR_SESSION_EXPIRED,
)
from codestrata_platform.community_cloud_api.insights_auth.models import SessionClaims
from codestrata_platform.community_cloud_api.insights_auth.policy import SESSION_VERSION


class SessionError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def create_session_token(
    *,
    signing_secret: str,
    ttl_seconds: int,
    now: Callable[[], int] | None = None,
    session_version: int = SESSION_VERSION,
) -> str:
    clock = now or (lambda: int(time.time()))
    iat = int(clock())
    claims = {
        "authenticated": True,
        "exp": iat + int(ttl_seconds),
        "iat": iat,
        "sv": int(session_version),
    }
    body = _b64url_encode(
        json.dumps(claims, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    sig = _sign(body, signing_secret)
    return f"v1.{body}.{sig}"


def validate_session_token(
    token: str,
    *,
    signing_secret: str,
    now: Callable[[], int] | None = None,
    expected_version: int = SESSION_VERSION,
) -> SessionClaims:
    clock = now or (lambda: int(time.time()))
    if not token or not isinstance(token, str):
        raise SessionError(ERROR_INVALID_SESSION)
    parts = token.strip().split(".")
    if len(parts) != 3 or parts[0] != "v1":
        raise SessionError(ERROR_INVALID_SESSION)
    body, sig = parts[1], parts[2]
    expected_sig = _sign(body, signing_secret)
    if not hmac.compare_digest(sig, expected_sig):
        raise SessionError(ERROR_INVALID_SESSION)
    try:
        payload: dict[str, Any] = json.loads(_b64url_decode(body).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise SessionError(ERROR_INVALID_SESSION) from None

    if payload.get("authenticated") is not True:
        raise SessionError(ERROR_INVALID_SESSION)
    try:
        iat = int(payload["iat"])
        exp = int(payload["exp"])
        sv = int(payload["sv"])
    except (KeyError, TypeError, ValueError):
        raise SessionError(ERROR_INVALID_SESSION) from None
    if sv != expected_version:
        raise SessionError(ERROR_INVALID_SESSION)
    now_ts = int(clock())
    if iat > now_ts + 60:
        # Future-issued beyond small skew → invalid.
        raise SessionError(ERROR_INVALID_SESSION)
    if now_ts >= exp:
        raise SessionError(ERROR_SESSION_EXPIRED)
    if exp <= iat:
        raise SessionError(ERROR_INVALID_SESSION)
    return SessionClaims(authenticated=True, iat=iat, exp=exp, sv=sv)


def _sign(body: str, signing_secret: str) -> str:
    digest = hmac.new(
        signing_secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)
