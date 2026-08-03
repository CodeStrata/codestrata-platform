"""Community Cloud API client authentication (Slice 7.13).

Verifies possession of an issued Community client credential. Does not identify
a human user, authorize repository access, or establish billing relationships.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.authentication.decisions import (
    DECISION_AUTHENTICATED,
    DECISION_INACTIVE,
    DECISION_INVALID,
    DECISION_MISSING,
    DECISION_SCOPE_MISMATCH,
    DECISION_UNAVAILABLE,
    AuthenticationDecision,
)
from codestrata_platform.community_cloud_api.authentication.diagnostics import (
    AuthenticationDiagnostics,
)
from codestrata_platform.community_cloud_api.authentication.middleware import (
    AuthenticationRuntime,
)
from codestrata_platform.community_cloud_api.authentication.models import (
    AUTH_GROUP_COMMUNITY_INGESTION,
    AUTH_GROUP_PUBLIC,
    COMMUNITY_AUTHENTICATION_POLICY_ID,
    COMMUNITY_AUTHENTICATION_POLICY_URN,
    COMMUNITY_AUTHENTICATION_POLICY_VERSION,
    COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION,
    CREDENTIAL_PREFIX,
    AuthenticatedCommunityClient,
    CommunityAuthenticationPolicy,
)
from codestrata_platform.community_cloud_api.authentication.policy import (
    ACTIVE_AUTHENTICATION_POLICY,
    default_authentication_policy,
    validate_authentication_policy,
)
from codestrata_platform.community_cloud_api.authentication.ports import (
    CommunityCredentialVerifier,
    CredentialVerificationResult,
    UnavailableCommunityCredentialVerifier,
)
from codestrata_platform.community_cloud_api.authentication.verifier import (
    InMemoryCommunityCredentialVerifier,
)

__all__ = [
    "ACTIVE_AUTHENTICATION_POLICY",
    "AUTH_GROUP_COMMUNITY_INGESTION",
    "AUTH_GROUP_PUBLIC",
    "COMMUNITY_AUTHENTICATION_POLICY_ID",
    "COMMUNITY_AUTHENTICATION_POLICY_URN",
    "COMMUNITY_AUTHENTICATION_POLICY_VERSION",
    "COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION",
    "CREDENTIAL_PREFIX",
    "DECISION_AUTHENTICATED",
    "DECISION_INACTIVE",
    "DECISION_INVALID",
    "DECISION_MISSING",
    "DECISION_SCOPE_MISMATCH",
    "DECISION_UNAVAILABLE",
    "AuthenticatedCommunityClient",
    "AuthenticationDecision",
    "AuthenticationDiagnostics",
    "AuthenticationRuntime",
    "CommunityAuthenticationPolicy",
    "CommunityCredentialVerifier",
    "CredentialVerificationResult",
    "InMemoryCommunityCredentialVerifier",
    "UnavailableCommunityCredentialVerifier",
    "default_authentication_policy",
    "validate_authentication_policy",
]
