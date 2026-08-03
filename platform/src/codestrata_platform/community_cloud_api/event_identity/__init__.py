"""Retry-safe event identity foundation (Slice 7.6)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.event_identity.decisions import (
    classify_retry,
)
from codestrata_platform.community_cloud_api.event_identity.diagnostics import (
    EventIdentityDiagnostic,
    build_event_identity_diagnostic,
)
from codestrata_platform.community_cloud_api.event_identity.fingerprint import (
    FingerprintError,
    compute_payload_fingerprint,
)
from codestrata_platform.community_cloud_api.event_identity.identifiers import (
    build_event_key,
    build_safe_event_reference,
)
from codestrata_platform.community_cloud_api.event_identity.models import (
    COMMUNITY_EVENT_IDENTITY_POLICY_URN,
    COMMUNITY_EVENT_IDENTITY_POLICY_VERSION,
    CommunityEventIdentityPolicy,
    EventIdentityScope,
    IdempotencyOutcome,
    RetryDecision,
    RetryStatus,
    StoredEventIdentity,
)
from codestrata_platform.community_cloud_api.event_identity.policy import (
    ACTIVE_EVENT_IDENTITY_POLICY,
    default_event_identity_policy,
)
from codestrata_platform.community_cloud_api.event_identity.ports import (
    EventIdentityLookup,
    EventIdentityRecorder,
    InMemoryEventIdentityStore,
)
from codestrata_platform.community_cloud_api.event_identity.registry import (
    evaluate_event_identity,
    record_if_first_seen,
)
from codestrata_platform.community_cloud_api.event_identity.validation import (
    build_event_identity_conflict_error,
    validate_event_id_text,
    validate_installation_id_text,
)
from codestrata_platform.community_cloud_api.validation.schema import (
    ApiEventId,
    ApiInstallationId,
)

__all__ = [
    "ACTIVE_EVENT_IDENTITY_POLICY",
    "COMMUNITY_EVENT_IDENTITY_POLICY_URN",
    "COMMUNITY_EVENT_IDENTITY_POLICY_VERSION",
    "ApiEventId",
    "ApiInstallationId",
    "CommunityEventIdentityPolicy",
    "EventIdentityDiagnostic",
    "EventIdentityLookup",
    "EventIdentityRecorder",
    "EventIdentityScope",
    "FingerprintError",
    "IdempotencyOutcome",
    "InMemoryEventIdentityStore",
    "RetryDecision",
    "RetryStatus",
    "StoredEventIdentity",
    "build_event_identity_conflict_error",
    "build_event_identity_diagnostic",
    "build_event_key",
    "build_safe_event_reference",
    "classify_retry",
    "compute_payload_fingerprint",
    "default_event_identity_policy",
    "evaluate_event_identity",
    "record_if_first_seen",
    "validate_event_id_text",
    "validate_installation_id_text",
]
