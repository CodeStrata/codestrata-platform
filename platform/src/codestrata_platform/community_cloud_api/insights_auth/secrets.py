"""Secrets Manager port — identifiers only in config; values never logged."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.community_cloud_api.insights_auth.policy import (
    DEFAULT_PASSWORD_SECRET_ID,
    DEFAULT_SESSION_SECRET_ID,
)


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
    """Bounded warm-runtime cache for session signing secret (not password)."""

    def __init__(
        self,
        inner: SecretsPort,
        *,
        cacheable_ids: frozenset[str] | None = None,
    ) -> None:
        self._inner = inner
        self._cache: dict[str, str] = {}
        self._cacheable = cacheable_ids or frozenset({DEFAULT_SESSION_SECRET_ID})

    def get_secret_value(self, secret_id: str) -> str | None:
        if secret_id in self._cacheable and secret_id in self._cache:
            return self._cache[secret_id]
        value = self._inner.get_secret_value(secret_id)
        if value is not None and secret_id in self._cacheable:
            self._cache[secret_id] = value
        return value


# Test-only fixture identifiers — must not match production secret values.
TEST_PASSWORD_PLAINTEXT = "test-only-insights-password-NOT-PRODUCTION"
TEST_SESSION_SECRET = "test-only-session-signing-secret-NOT-PRODUCTION-32b"

__all__ = [
    "CachingSecretsPort",
    "DEFAULT_PASSWORD_SECRET_ID",
    "DEFAULT_SESSION_SECRET_ID",
    "FakeSecretsPort",
    "SecretsPort",
    "TEST_PASSWORD_PLAINTEXT",
    "TEST_SESSION_SECRET",
    "UnavailableSecretsPort",
]
