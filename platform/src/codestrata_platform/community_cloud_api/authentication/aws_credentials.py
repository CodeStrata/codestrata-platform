"""AWS Secrets Manager backed Community credential verifier (Slice 17.7).

Secret JSON stores fingerprint records only — never raw ``cscc_v1_`` tokens.
Fail-closed on missing or malformed secrets.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from codestrata_platform.community_cloud_api.authentication.credentials import (
    CommunityClientCredential,
    constant_time_equal,
    fingerprint_credential,
)
from codestrata_platform.community_cloud_api.authentication.models import (
    ALLOWED_CLIENT_TYPES,
    CREDENTIAL_STATUS_ACTIVE,
    CREDENTIAL_STATUS_INACTIVE,
    CREDENTIAL_STATUS_REVOKED,
    VALID_CREDENTIAL_STATUSES,
    CommunityAuthenticationPolicy,
    CommunityCredentialRecord,
)
from codestrata_platform.community_cloud_api.authentication.policy import (
    default_authentication_policy,
)
from codestrata_platform.community_cloud_api.authentication.ports import (
    CredentialVerificationResult,
)

DEFAULT_COMMUNITY_CREDENTIALS_SECRET_ID = "codestrata/community/client-credentials"
DEFAULT_CREDENTIALS_CACHE_TTL_SECONDS = 60.0


class CommunityCredentialsSecretsPort(Protocol):
    def get_secret_value(self, secret_id: str) -> str | None:
        """Return secret string or None when missing. Never log the value."""
        ...


class AwsCommunityCredentialsSecretsPort:
    """Lazy boto3 Secrets Manager reader — mirrors Insights AwsSecretsPort."""

    def __init__(self, *, client: Any | None = None, region_name: str | None = None) -> None:
        self._client = client
        self._region_name = region_name

    def _sm(self) -> Any:
        if self._client is not None:
            return self._client
        import boto3

        kwargs: dict[str, str] = {}
        if self._region_name:
            kwargs["region_name"] = self._region_name
        self._client = boto3.client("secretsmanager", **kwargs)
        return self._client

    def get_secret_value(self, secret_id: str) -> str | None:
        if not secret_id or not str(secret_id).strip():
            return None
        try:
            response = self._sm().get_secret_value(SecretId=secret_id)
        except Exception:  # noqa: BLE001 — fail-closed; do not leak ARNs/values
            return None
        if "SecretString" in response and response["SecretString"] is not None:
            return str(response["SecretString"])
        binary = response.get("SecretBinary")
        if binary is None:
            return None
        if isinstance(binary, (bytes, bytearray)):
            return bytes(binary).decode("utf-8")
        return None


@dataclass
class CachingCommunityCredentialsSecretsPort:
    """Short-TTL cache for credentials JSON (fingerprints only)."""

    inner: CommunityCredentialsSecretsPort
    ttl_seconds: float = DEFAULT_CREDENTIALS_CACHE_TTL_SECONDS
    _cache: dict[str, tuple[float, str]] = field(default_factory=dict)

    def get_secret_value(self, secret_id: str) -> str | None:
        now = time.monotonic()
        cached = self._cache.get(secret_id)
        if cached is not None:
            expires_at, value = cached
            if now < expires_at:
                return value
            self._cache.pop(secret_id, None)
        value = self.inner.get_secret_value(secret_id)
        if value is not None and self.ttl_seconds > 0:
            self._cache[secret_id] = (now + self.ttl_seconds, value)
        return value


def parse_community_credentials_secret(
    raw: str,
) -> dict[str, CommunityCredentialRecord] | None:
    """Parse fingerprint-only credentials JSON. Returns None when malformed."""

    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    items = data.get("credentials")
    if not isinstance(items, list):
        return None
    records: dict[str, CommunityCredentialRecord] = {}
    for item in items:
        if not isinstance(item, dict):
            return None
        try:
            fingerprint = str(item.get("credential_fingerprint") or "").strip()
            client_id = str(item.get("client_id") or "").strip()
            client_type = str(item.get("client_type") or "").strip()
            credential_id = str(item.get("credential_id") or "").strip()
            rate_limit_scope_id = str(item.get("rate_limit_scope_id") or "").strip()
            status = str(item.get("status") or "").strip()
            credential_version = str(item.get("credential_version") or "1").strip()
            groups_raw = item.get("allowed_route_groups") or ["ingestion"]
            if not isinstance(groups_raw, list):
                return None
            allowed_route_groups = tuple(str(g).strip() for g in groups_raw if str(g).strip())
            if fingerprint.startswith("cscc_v1_") or "cscc_v1_" in fingerprint:
                # Raw tokens must never appear in the secret.
                return None
            if not fingerprint.startswith("cred:"):
                return None
            if client_type not in ALLOWED_CLIENT_TYPES:
                return None
            if status not in VALID_CREDENTIAL_STATUSES:
                return None
            record = CommunityCredentialRecord(
                credential_fingerprint=fingerprint,
                client_id=client_id,
                client_type=client_type,
                credential_version=credential_version,
                status=status,
                allowed_route_groups=allowed_route_groups,
                rate_limit_scope_id=rate_limit_scope_id,
                credential_id=credential_id,
            )
        except (TypeError, ValueError):
            return None
        records[fingerprint] = record
    return records


@dataclass
class AwsCommunityCredentialVerifier:
    """Verify Community client credentials against Secrets Manager fingerprints."""

    secrets: CommunityCredentialsSecretsPort
    secret_id: str = DEFAULT_COMMUNITY_CREDENTIALS_SECRET_ID
    policy: CommunityAuthenticationPolicy = field(
        default_factory=default_authentication_policy
    )

    def _load_records(self) -> dict[str, CommunityCredentialRecord] | None:
        raw = self.secrets.get_secret_value(self.secret_id)
        if raw is None:
            return None
        return parse_community_credentials_secret(raw)

    def verify(self, credential: CommunityClientCredential) -> CredentialVerificationResult:
        try:
            computed = fingerprint_credential(credential.token, policy=self.policy)
        except Exception:  # noqa: BLE001
            return CredentialVerificationResult(status="unavailable")

        records = self._load_records()
        if records is None:
            return CredentialVerificationResult(
                status="unavailable",
                limitations=("credential_verifier_unavailable",),
            )

        matched: CommunityCredentialRecord | None = None
        for stored_fp, record in records.items():
            if constant_time_equal(stored_fp, computed):
                matched = record
                break
        if matched is None:
            _ = constant_time_equal(computed, "cred:" + ("0" * 64))
            return CredentialVerificationResult(status="unknown")

        if matched.status == CREDENTIAL_STATUS_ACTIVE:
            return CredentialVerificationResult(status="active", record=matched)
        if matched.status == CREDENTIAL_STATUS_INACTIVE:
            return CredentialVerificationResult(status="inactive", record=matched)
        if matched.status == CREDENTIAL_STATUS_REVOKED:
            return CredentialVerificationResult(status="revoked", record=matched)
        return CredentialVerificationResult(status="unknown")


def build_production_credential_verifier(
    *,
    environ: dict[str, str] | None = None,
    secrets: CommunityCredentialsSecretsPort | None = None,
) -> AwsCommunityCredentialVerifier:
    """Build production credential verifier from env + Secrets Manager."""

    env = environ if environ is not None else dict(os.environ)
    secret_id = (
        env.get("CODESTRATA_COMMUNITY_CREDENTIALS_SECRET_ID")
        or DEFAULT_COMMUNITY_CREDENTIALS_SECRET_ID
    ).strip()
    if secrets is None:
        region = (env.get("AWS_REGION") or env.get("AWS_DEFAULT_REGION") or "").strip() or None
        inner: CommunityCredentialsSecretsPort = AwsCommunityCredentialsSecretsPort(
            region_name=region
        )
        secrets = CachingCommunityCredentialsSecretsPort(inner=inner)
    return AwsCommunityCredentialVerifier(secrets=secrets, secret_id=secret_id)


__all__ = [
    "DEFAULT_COMMUNITY_CREDENTIALS_SECRET_ID",
    "DEFAULT_CREDENTIALS_CACHE_TTL_SECONDS",
    "AwsCommunityCredentialVerifier",
    "AwsCommunityCredentialsSecretsPort",
    "CachingCommunityCredentialsSecretsPort",
    "CommunityCredentialsSecretsPort",
    "build_production_credential_verifier",
    "parse_community_credentials_secret",
]
