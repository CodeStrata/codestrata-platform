"""Engine telemetry inventory helpers for verification (imports Engine only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata.telemetry.consent import (
    allow_session_consent,
    default_session_consent,
    deny_session_consent,
    non_interactive_session_consent,
)
from codestrata.telemetry.decisions import TelemetryDecision, is_transmission_allowed
from codestrata.telemetry.events import APPROVED_RUNTIME_EVENT_TYPES
from codestrata.telemetry.privacy import APPROVED_FIELD_NAMES, FORBIDDEN_FIELD_NAMES
from codestrata.telemetry.catalog_metadata import NEVER_COLLECTED
from codestrata.telemetry.runtime_policy import (
    COMMUNITY_TELEMETRY_RUNTIME_POLICY_URN,
    PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_URN,
    PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_VERSION,
    COMMUNITY_TELEMETRY_RUNTIME_POLICY_VERSION,
    default_runtime_policy,
)


@dataclass(frozen=True, slots=True)
class EngineTelemetryInventory:
    runtime_policy_urn: str
    runtime_policy_version: str
    event_schema_urn: str
    event_schema_version: str
    client_name: str
    approved_event_types: tuple[str, ...]
    approved_field_names: frozenset[str]
    forbidden_field_names: frozenset[str]
    never_collected: tuple[str, ...]
    disabled_by_default: bool
    installation_id_allowed: bool
    transport_unavailable_by_default: bool


def load_engine_inventory() -> EngineTelemetryInventory:
    policy = default_runtime_policy()
    return EngineTelemetryInventory(
        runtime_policy_urn=COMMUNITY_TELEMETRY_RUNTIME_POLICY_URN,
        runtime_policy_version=COMMUNITY_TELEMETRY_RUNTIME_POLICY_VERSION,
        event_schema_urn=PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_URN,
        event_schema_version=PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_VERSION,
        client_name="codestrata_cli",
        approved_event_types=tuple(sorted(APPROVED_RUNTIME_EVENT_TYPES)),
        approved_field_names=APPROVED_FIELD_NAMES,
        forbidden_field_names=FORBIDDEN_FIELD_NAMES,
        never_collected=tuple(sorted(name for name, _desc in NEVER_COLLECTED)),
        disabled_by_default=bool(policy.disabled_by_default),
        installation_id_allowed=bool(policy.installation_id_allowed),
        transport_unavailable_by_default=bool(policy.transport_unavailable_by_default),
    )


def engine_consent_snapshot() -> dict[str, Any]:
    default = default_session_consent()
    allowed = allow_session_consent()
    denied = deny_session_consent()
    non_interactive = non_interactive_session_consent()
    return {
        "default_decision": default.decision.value,
        "default_persisted": False,
        "default_transmission": is_transmission_allowed(default.decision),
        "allow_decision": allowed.decision.value,
        "allow_transmission": is_transmission_allowed(allowed.decision),
        "deny_decision": denied.decision.value,
        "deny_transmission": is_transmission_allowed(denied.decision),
        "non_interactive_decision": non_interactive.decision.value,
        "decisions": sorted(d.value for d in TelemetryDecision if d != TelemetryDecision.TRANSPORT_UNAVAILABLE),
    }
