"""Secrets Manager port — identifiers only in config; values never logged."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol

from codestrata_platform.community_cloud_api.insights_auth.policy import (
    DEFAULT_PASSWORD_SECRET_ID,
    DEFAULT_SESSION_SECRET_ID,
)

# Session signing secret may be warm-cached. Password verifier is never cached.
DEFAULT_SESSION_SECRET_CACHE_TTL_SECONDS = 300


class SecretsPort(Protocol):
    def get_secret_value(self, secret_id: str) -> str | None:
        """Return secret string or None when missing. Never log the value."""
        ...


class UnavailableSecretsPort:
    """Fail-closed default — login cannot succeed."""

    def get_secret_value(self, secret_id: str) -> str | None:
        _ = secret_id
        return None


class FakeSecretsPort:
    """In-memory secrets for tests — synthetic values only."""

    def __init__(self, secrets: dict[str, str] | None = None) -> None:
        self._secrets = dict(secrets or {})
        self.get_calls: list[str] = []

    def put(self, secret_id: str, value: str) -> None:
        self._secrets[secret_id] = value

    def get_secret_value(self, secret_id: str) -> str | None:
        self.get_calls.append(secret_id)
        return self._secrets.get(secret_id)


class CachingSecretsPort:
    """Bounded warm-runtime cache for session signing secret (not password).

    Password verifier IDs must never be listed in ``cacheable_ids``. Session
    secret entries expire after ``ttl_seconds`` so rotation becomes effective
    without requiring a Lambda cold start (worst case: TTL window).
    """

    def __init__(
        self,
        inner: SecretsPort,
        *,
        cacheable_ids: frozenset[str] | None = None,
        ttl_seconds: int = DEFAULT_SESSION_SECRET_CACHE_TTL_SECONDS,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self._inner = inner
        self._cache: dict[str, tuple[str, float]] = {}
        self._cacheable = cacheable_ids or frozenset({DEFAULT_SESSION_SECRET_ID})
        self._ttl_seconds = max(0, int(ttl_seconds))
        self._monotonic = monotonic or time.monotonic

    def get_secret_value(self, secret_id: str) -> str | None:
        if secret_id in self._cacheable and secret_id in self._cache:
            value, expires_at = self._cache[secret_id]
            if self._ttl_seconds <= 0 or self._monotonic() < expires_at:
                return value
            del self._cache[secret_id]
        value = self._inner.get_secret_value(secret_id)
        if value is not None and secret_id in self._cacheable:
            expires_at = self._monotonic() + float(self._ttl_seconds)
            self._cache[secret_id] = (value, expires_at)
        return value


# Test-only fixture identifiers — must not match production secret values.
TEST_PASSWORD_PLAINTEXT = "test-only-insights-password-NOT-PRODUCTION"
TEST_SESSION_SECRET = "test-only-session-signing-secret-NOT-PRODUCTION-32b"

__all__ = [
    "CachingSecretsPort",
    "DEFAULT_PASSWORD_SECRET_ID",
    "DEFAULT_SESSION_SECRET_CACHE_TTL_SECONDS",
    "DEFAULT_SESSION_SECRET_ID",
    "FakeSecretsPort",
    "SecretsPort",
    "TEST_PASSWORD_PLAINTEXT",
    "TEST_SESSION_SECRET",
    "UnavailableSecretsPort",
    "build_production_secrets_port",
]


def build_production_secrets_port(
    *,
    environ: dict[str, str] | None = None,
) -> SecretsPort:
    """Select Insights secrets port for production wiring.

    When ``CODESTRATA_INSIGHTS_SECRETS_BACKEND=aws`` (Slice 17.6+), use AWS
    Secrets Manager. Otherwise remain fail-closed (UnavailableSecretsPort).
    Secret *values* are never read from environment variables.
    """

    import os

    env = environ if environ is not None else dict(os.environ)
    backend = (env.get("CODESTRATA_INSIGHTS_SECRETS_BACKEND") or "").strip().lower()
    if backend != "aws":
        return UnavailableSecretsPort()
    from codestrata_platform.community_cloud_api.insights_auth.aws_secrets import (
        AwsSecretsPort,
    )

    region = (env.get("AWS_REGION") or env.get("AWS_DEFAULT_REGION") or "").strip() or None
    inner = AwsSecretsPort(region_name=region)
    session_id = (
        env.get("CODESTRATA_INSIGHTS_SESSION_SECRET_ID") or DEFAULT_SESSION_SECRET_ID
    ).strip()
    return CachingSecretsPort(
        inner,
        cacheable_ids=frozenset({session_id}),
        ttl_seconds=DEFAULT_SESSION_SECRET_CACHE_TTL_SECONDS,
    )

