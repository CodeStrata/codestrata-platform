"""Persistence-neutral credential verification ports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from codestrata_platform.community_cloud_api.authentication.credentials import (
    CommunityClientCredential,
)
from codestrata_platform.community_cloud_api.authentication.models import (
    CommunityCredentialRecord,
)


@dataclass(frozen=True, slots=True)
class CredentialVerificationResult:
    status: str  # active | unknown | inactive | revoked | unavailable
    record: CommunityCredentialRecord | None = None
    limitations: tuple[str, ...] = ()


class CommunityCredentialVerifier(Protocol):
    def verify(self, credential: CommunityClientCredential) -> CredentialVerificationResult: ...


class UnavailableCommunityCredentialVerifier:
    """Default fail-closed verifier — protected routes return 503."""

    def verify(self, credential: CommunityClientCredential) -> CredentialVerificationResult:
        _ = credential
        return CredentialVerificationResult(
            status="unavailable",
            limitations=("credential_verifier_unavailable",),
        )
