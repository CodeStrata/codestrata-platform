"""In-memory and helper credential verification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from codestrata_platform.community_cloud_api.authentication.credentials import (
    CommunityClientCredential,
    constant_time_equal,
    fingerprint_credential,
)
from codestrata_platform.community_cloud_api.authentication.models import (
    CREDENTIAL_STATUS_ACTIVE,
    CREDENTIAL_STATUS_INACTIVE,
    CREDENTIAL_STATUS_REVOKED,
    CommunityAuthenticationPolicy,
    CommunityCredentialRecord,
)
from codestrata_platform.community_cloud_api.authentication.ports import (
    CredentialVerificationResult,
)
from codestrata_platform.community_cloud_api.authentication.policy import (
    default_authentication_policy,
)


@dataclass
class InMemoryCommunityCredentialVerifier:
    """Test/local verifier — stores fingerprints only, never plaintext tokens."""

    policy: CommunityAuthenticationPolicy = field(
        default_factory=default_authentication_policy
    )
    _records: dict[str, CommunityCredentialRecord] = field(default_factory=dict)

    def register(
        self,
        token: str,
        *,
        client_id: str,
        client_type: str,
        rate_limit_scope_id: str,
        credential_id: str,
        status: str = CREDENTIAL_STATUS_ACTIVE,
        allowed_route_groups: tuple[str, ...] = ("ingestion",),
        credential_version: str = "1",
    ) -> CommunityCredentialRecord:
        fp = fingerprint_credential(token, policy=self.policy)
        record = CommunityCredentialRecord(
            credential_fingerprint=fp,
            client_id=client_id,
            client_type=client_type,
            credential_version=credential_version,
            status=status,
            allowed_route_groups=allowed_route_groups,
            rate_limit_scope_id=rate_limit_scope_id,
            credential_id=credential_id,
        )
        self._records[fp] = record
        return record

    def verify(self, credential: CommunityClientCredential) -> CredentialVerificationResult:
        try:
            computed = fingerprint_credential(credential.token, policy=self.policy)
        except Exception:  # noqa: BLE001
            return CredentialVerificationResult(status="unavailable")

        matched: CommunityCredentialRecord | None = None
        for stored_fp, record in self._records.items():
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

    def has_plaintext(self) -> bool:
        blob = str(self._records)
        return "cscc_v1_" in blob


def build_safe_client_reference(
    *,
    client_id: str,
    policy: CommunityAuthenticationPolicy,
) -> str:
    digest = hashlib.sha256(
        f"{policy.policy_token()}|{client_id}".encode("utf-8")
    ).hexdigest()
    length = policy.safe_client_reference_length
    return f"client-{digest[:length]}"
