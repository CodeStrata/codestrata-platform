"""Community Cloud client authentication models and policy (Slice 7.13)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


COMMUNITY_AUTHENTICATION_POLICY_ID = "community-authentication-policy"
COMMUNITY_AUTHENTICATION_POLICY_VERSION = "1.0"
COMMUNITY_AUTHENTICATION_POLICY_URN = (
    f"{COMMUNITY_AUTHENTICATION_POLICY_ID}:{COMMUNITY_AUTHENTICATION_POLICY_VERSION}"
)

COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION = "1"
CREDENTIAL_PREFIX = "cscc_v1_"

AUTH_GROUP_PUBLIC = "public"
AUTH_GROUP_COMMUNITY_INGESTION = "community_ingestion"
VALID_AUTH_GROUPS = frozenset({AUTH_GROUP_PUBLIC, AUTH_GROUP_COMMUNITY_INGESTION})

ACCEPTED_SCHEME_BEARER = "Bearer"

CLIENT_TYPE_CLI = "codestrata_cli"
CLIENT_TYPE_VSCODE = "vscode_extension"
CLIENT_TYPE_CURSOR = "cursor_extension"
ALLOWED_CLIENT_TYPES = frozenset(
    {CLIENT_TYPE_CLI, CLIENT_TYPE_VSCODE, CLIENT_TYPE_CURSOR}
)

ROUTE_GROUP_INGESTION = "ingestion"
ROUTE_GROUP_HEALTH_PUBLIC = "health_public"

PUBLIC_ROUTE_IDS: tuple[str, ...] = ("health.get",)
PROTECTED_ROUTE_IDS: tuple[str, ...] = (
    "telemetry.ingest",
    "assessment_metadata.ingest",
    "cli_events.ingest",
    "extension_events.ingest",
    "ai_usage.ingest",
)
PRODUCTION_ROUTE_IDS: tuple[str, ...] = PUBLIC_ROUTE_IDS + PROTECTED_ROUTE_IDS

CREDENTIAL_STATUS_ACTIVE = "active"
CREDENTIAL_STATUS_INACTIVE = "inactive"
CREDENTIAL_STATUS_REVOKED = "revoked"
VALID_CREDENTIAL_STATUSES = frozenset(
    {
        CREDENTIAL_STATUS_ACTIVE,
        CREDENTIAL_STATUS_INACTIVE,
        CREDENTIAL_STATUS_REVOKED,
    }
)

DEFAULT_CREDENTIAL_MIN_LENGTH = 24
DEFAULT_CREDENTIAL_MAX_LENGTH = 128
DEFAULT_SAFE_CLIENT_REF_LENGTH = 12


@dataclass(frozen=True, slots=True)
class CommunityAuthenticationPolicy:
    """Deterministic Community Cloud client-authentication policy (v1.0)."""

    policy_id: str = COMMUNITY_AUTHENTICATION_POLICY_ID
    policy_version: str = COMMUNITY_AUTHENTICATION_POLICY_URN
    enabled: bool = True
    public_route_ids: tuple[str, ...] = PUBLIC_ROUTE_IDS
    protected_route_ids: tuple[str, ...] = PROTECTED_ROUTE_IDS
    accepted_scheme: str = ACCEPTED_SCHEME_BEARER
    credential_format_version: str = COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION
    credential_min_length: int = DEFAULT_CREDENTIAL_MIN_LENGTH
    credential_max_length: int = DEFAULT_CREDENTIAL_MAX_LENGTH
    credential_prefix: str = CREDENTIAL_PREFIX
    invalid_credential_behavior: str = "generic_401"
    verifier_unavailable_behavior: str = "fail_closed_503"
    rate_limit_scope_behavior: str = "authenticated_primary"
    include_www_authenticate_on_401: bool = True
    ignore_authorization_on_public_routes: bool = True
    enforce_client_payload_match: bool = True
    safe_client_reference_length: int = DEFAULT_SAFE_CLIENT_REF_LENGTH
    limitations: tuple[str, ...] = (
        "client_credential_auth_only",
        "no_user_identity",
        "no_organization_identity",
        "no_credential_issuance_api",
        "no_production_credential_store",
        "in_memory_verifier_for_tests_only",
        "installation_id_is_not_authentication",
    )

    def __post_init__(self) -> None:
        if self.policy_id != COMMUNITY_AUTHENTICATION_POLICY_ID:
            raise ValueError("unsupported authentication policy id")
        if self.policy_version != COMMUNITY_AUTHENTICATION_POLICY_URN:
            raise ValueError("unsupported authentication policy version")
        if self.accepted_scheme != ACCEPTED_SCHEME_BEARER:
            raise ValueError("only Bearer scheme is supported")
        if self.credential_format_version != COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION:
            raise ValueError("unsupported credential format version")
        if self.credential_prefix != CREDENTIAL_PREFIX:
            raise ValueError("unsupported credential prefix")
        if int(self.credential_min_length) < len(CREDENTIAL_PREFIX) + 8:
            raise ValueError("credential_min_length too small")
        if int(self.credential_max_length) < int(self.credential_min_length):
            raise ValueError("credential_max_length must be >= min")
        if int(self.safe_client_reference_length) < 8:
            raise ValueError("safe_client_reference_length too small")
        if self.verifier_unavailable_behavior != "fail_closed_503":
            raise ValueError("invalid verifier_unavailable_behavior")
        if self.rate_limit_scope_behavior != "authenticated_primary":
            raise ValueError("invalid rate_limit_scope_behavior")
        public = tuple(sorted(str(item).strip() for item in self.public_route_ids))
        protected = tuple(sorted(str(item).strip() for item in self.protected_route_ids))
        if set(public) & set(protected):
            raise ValueError("duplicate route authentication classification")
        if set(public) != set(PUBLIC_ROUTE_IDS):
            raise ValueError("health.get must be the sole public production route")
        if set(protected) != set(PROTECTED_ROUTE_IDS):
            raise ValueError("all five ingestion routes must be protected")
        classified = set(public) | set(protected)
        if classified != set(PRODUCTION_ROUTE_IDS):
            raise ValueError("every production route must be classified")
        object.__setattr__(self, "public_route_ids", public)
        object.__setattr__(self, "protected_route_ids", protected)
        object.__setattr__(self, "credential_min_length", int(self.credential_min_length))
        object.__setattr__(self, "credential_max_length", int(self.credential_max_length))
        object.__setattr__(
            self, "safe_client_reference_length", int(self.safe_client_reference_length)
        )
        object.__setattr__(
            self,
            "limitations",
            tuple(sorted(str(item) for item in self.limitations)),
        )

    @classmethod
    def default(cls) -> CommunityAuthenticationPolicy:
        return cls()

    def policy_token(self) -> str:
        return self.policy_version

    def is_public_route(self, route_id: str) -> bool:
        return route_id in self.public_route_ids

    def is_protected_route(self, route_id: str) -> bool:
        return route_id in self.protected_route_ids

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "accepted_scheme": self.accepted_scheme,
            "credential_format_version": self.credential_format_version,
            "credential_max_length": self.credential_max_length,
            "credential_min_length": self.credential_min_length,
            "credential_prefix": self.credential_prefix,
            "enabled": self.enabled,
            "enforce_client_payload_match": self.enforce_client_payload_match,
            "ignore_authorization_on_public_routes": (
                self.ignore_authorization_on_public_routes
            ),
            "include_www_authenticate_on_401": self.include_www_authenticate_on_401,
            "invalid_credential_behavior": self.invalid_credential_behavior,
            "limitations": list(self.limitations),
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "protected_route_ids": list(self.protected_route_ids),
            "public_route_ids": list(self.public_route_ids),
            "rate_limit_scope_behavior": self.rate_limit_scope_behavior,
            "safe_client_reference_length": self.safe_client_reference_length,
            "verifier_unavailable_behavior": self.verifier_unavailable_behavior,
        }


@dataclass(frozen=True, slots=True)
class AuthenticatedCommunityClient:
    """Opaque authenticated Community client principal — not a human identity."""

    client_id: str
    client_type: str
    credential_id: str
    credential_version: str
    status: str
    rate_limit_scope_id: str
    allowed_route_groups: tuple[str, ...] = (ROUTE_GROUP_INGESTION,)
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        client_id = (self.client_id or "").strip()
        client_type = (self.client_type or "").strip()
        credential_id = (self.credential_id or "").strip()
        rate_limit_scope_id = (self.rate_limit_scope_id or "").strip()
        if not client_id or not credential_id or not rate_limit_scope_id:
            raise ValueError("opaque client identity fields are required")
        if client_type not in ALLOWED_CLIENT_TYPES:
            raise ValueError(f"unsupported client_type: {client_type}")
        if self.status != CREDENTIAL_STATUS_ACTIVE:
            raise ValueError("principal status must be active")
        groups = tuple(sorted(str(item) for item in self.allowed_route_groups))
        if ROUTE_GROUP_INGESTION not in groups and groups:
            pass
        object.__setattr__(self, "client_id", client_id)
        object.__setattr__(self, "client_type", client_type)
        object.__setattr__(self, "credential_id", credential_id)
        object.__setattr__(self, "credential_version", str(self.credential_version))
        object.__setattr__(self, "rate_limit_scope_id", rate_limit_scope_id)
        object.__setattr__(self, "allowed_route_groups", groups)
        object.__setattr__(
            self,
            "limitations",
            tuple(sorted(str(item) for item in self.limitations)),
        )

    def to_stable_dict(self) -> dict[str, Any]:
        # Never include raw client_id / rate_limit_scope_id in public dumps.
        return {
            "client_type": self.client_type,
            "credential_version": self.credential_version,
            "limitations": list(self.limitations),
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class CommunityCredentialRecord:
    """Verifier-side credential record — fingerprint only, never plaintext."""

    credential_fingerprint: str
    client_id: str
    client_type: str
    credential_version: str
    status: str
    allowed_route_groups: tuple[str, ...]
    rate_limit_scope_id: str
    credential_id: str

    def __post_init__(self) -> None:
        if not (self.credential_fingerprint or "").startswith("cred:"):
            raise ValueError("credential_fingerprint must use cred: prefix")
        if self.client_type not in ALLOWED_CLIENT_TYPES:
            raise ValueError(f"unsupported client_type: {self.client_type}")
        if self.status not in VALID_CREDENTIAL_STATUSES:
            raise ValueError(f"invalid credential status: {self.status}")
        object.__setattr__(
            self,
            "allowed_route_groups",
            tuple(sorted(str(item) for item in self.allowed_route_groups)),
        )
