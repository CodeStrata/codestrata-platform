"""Bounded Community client credential value — never logged or public-serialized."""

from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass

from codestrata_platform.community_cloud_api.authentication.models import (
    COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION,
    CREDENTIAL_PREFIX,
    CommunityAuthenticationPolicy,
)

_TOKEN_BODY_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_PATHISH_RE = re.compile(r"(?i)(/|\\|://|file:|-----BEGIN)")


@dataclass(frozen=True)
class CommunityClientCredential:
    """Internal credential holder. ``repr`` is always redacted."""

    _token: str

    def __post_init__(self) -> None:
        # Prevent accidental public dumps via dataclass helpers.
        if not isinstance(self._token, str):
            raise TypeError("credential token must be a string")

    def __repr__(self) -> str:
        return "CommunityClientCredential([redacted])"

    def __str__(self) -> str:
        return "CommunityClientCredential([redacted])"

    @property
    def token(self) -> str:
        return self._token

    def release(self) -> None:
        """Drop strong reference semantics after verification (best-effort)."""

        object.__setattr__(self, "_token", "")


def parse_credential_token(
    raw: str,
    *,
    policy: CommunityAuthenticationPolicy,
) -> CommunityClientCredential | None:
    """Validate opaque token shape. Returns None when format is invalid."""

    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    if any(ch.isspace() for ch in text):
        return None
    if any(ord(ch) < 32 for ch in text):
        return None
    if "\n" in raw or "\r" in raw:
        return None
    if _PATHISH_RE.search(text):
        return None
    if len(text) < policy.credential_min_length or len(text) > policy.credential_max_length:
        return None
    if not text.startswith(policy.credential_prefix):
        return None
    body = text[len(policy.credential_prefix) :]
    if not body or not _TOKEN_BODY_RE.fullmatch(body):
        return None
    # Format version is embedded in prefix cscc_v1_
    if policy.credential_format_version != COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION:
        return None
    return CommunityClientCredential(_token=text)


def fingerprint_credential(
    token: str,
    *,
    policy: CommunityAuthenticationPolicy,
) -> str:
    """One-way credential fingerprint — never log or return publicly."""

    material = "|".join(
        (
            policy.policy_token(),
            policy.credential_format_version,
            CREDENTIAL_PREFIX,
            token,
        )
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"cred:{digest}"


def constant_time_equal(left: str, right: str) -> bool:
    """Constant-time string compare for secret-derived values."""

    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))
