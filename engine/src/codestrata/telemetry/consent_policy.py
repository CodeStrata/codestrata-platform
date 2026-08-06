"""Independent per-session telemetry consent policy (Slice 9.3).

Engine-local product-policy contract. Independent from runtime policy 1.0,
privacy-safe event schema 1.0, legacy TelemetryService schema 1.0.0, and
Community Cloud / Data Lake contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_ID = (
    "community-telemetry-session-consent-policy"
)
COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_VERSION = "1.0"
COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_URN = (
    f"{COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_ID}:"
    f"{COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_VERSION}"
)

_REVIEW_STATUS = "process_local_explicit_session_consent_only"

_LIMITATIONS: tuple[str, ...] = (
    "process_local_only",
    "no_persistence",
    "no_prior_consent_reuse",
    "no_installation_identity",
    "no_interactive_prompt_in_slice_9_3",
    "no_cli_flags_in_slice_9_3",
    "consent_does_not_imply_transport",
    "default_transport_unavailable",
    "legacy_preferences_separate",
)


class SessionConsentPolicyError(ValueError):
    """Raised when session-consent policy invariants fail."""


@dataclass(frozen=True, slots=True)
class CommunityTelemetrySessionConsentPolicy:
    """Deterministic, versioned per-session consent product-policy contract."""

    policy_id: str = COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_ID
    policy_version: str = COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_VERSION
    scope: str = "session"
    process_local: bool = True
    persistence_allowed: bool = False
    prior_consent_reuse_allowed: bool = False
    installation_identity_required: bool = False
    interactive_prompt_enabled: bool = False
    cli_flag_enabled: bool = False
    consent_implies_transport: bool = False
    review_status: str = _REVIEW_STATUS
    limitations: tuple[str, ...] = _LIMITATIONS

    def __post_init__(self) -> None:
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))
        self.validate()

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def validate(self) -> None:
        if self.policy_id != COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_ID:
            raise SessionConsentPolicyError("unsupported session consent policy id")
        if self.policy_version != COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_VERSION:
            raise SessionConsentPolicyError("unsupported session consent policy version")
        if self.scope != "session":
            raise SessionConsentPolicyError("consent scope must be session")
        if not self.process_local:
            raise SessionConsentPolicyError("process_local must be true")
        if self.persistence_allowed:
            raise SessionConsentPolicyError("persistence_allowed must be false")
        if self.prior_consent_reuse_allowed:
            raise SessionConsentPolicyError("prior_consent_reuse_allowed must be false")
        if self.installation_identity_required:
            raise SessionConsentPolicyError(
                "installation_identity_required must be false"
            )
        if self.interactive_prompt_enabled:
            raise SessionConsentPolicyError(
                "interactive_prompt_enabled must be false in Slice 9.3"
            )
        if self.cli_flag_enabled:
            raise SessionConsentPolicyError("cli_flag_enabled must be false in Slice 9.3")
        if self.consent_implies_transport:
            raise SessionConsentPolicyError("consent_implies_transport must be false")
        if self.review_status != _REVIEW_STATUS:
            raise SessionConsentPolicyError("unsupported review_status")

    @classmethod
    def default(cls) -> CommunityTelemetrySessionConsentPolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "cli_flag_enabled": self.cli_flag_enabled,
            "consent_implies_transport": self.consent_implies_transport,
            "installation_identity_required": self.installation_identity_required,
            "interactive_prompt_enabled": self.interactive_prompt_enabled,
            "limitations": list(self.limitations),
            "persistence_allowed": self.persistence_allowed,
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "prior_consent_reuse_allowed": self.prior_consent_reuse_allowed,
            "process_local": self.process_local,
            "review_status": self.review_status,
            "scope": self.scope,
        }


def default_session_consent_policy() -> CommunityTelemetrySessionConsentPolicy:
    return CommunityTelemetrySessionConsentPolicy.default()


__all__ = [
    "COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_ID",
    "COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_URN",
    "COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_VERSION",
    "CommunityTelemetrySessionConsentPolicy",
    "SessionConsentPolicyError",
    "default_session_consent_policy",
]
