"""Live Engine analytics inventory for Slice 10.8 verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata.telemetry.analytics.ai_analytics_catalogs import (
    APPROVED_AI_CAPABILITIES,
    APPROVED_AI_MODEL_FAMILIES,
    APPROVED_AI_OUTCOMES,
    APPROVED_AI_PROVIDER_FAMILIES,
)
from codestrata.telemetry.analytics.ai_analytics_policy import (
    COMMUNITY_AI_ANALYTICS_POLICY_URN,
    COMMUNITY_AI_ANALYTICS_SCHEMA_URN,
    default_ai_analytics_policy,
)
from codestrata.telemetry.analytics.assessment_analytics_policy import (
    COMMUNITY_ASSESSMENT_ANALYTICS_POLICY_URN,
    default_assessment_analytics_policy,
)
from codestrata.telemetry.analytics.events import (
    APPROVED_ANALYTICS_CATEGORIES,
    APPROVED_ANALYTICS_FIELD_NAMES,
    FORBIDDEN_ANALYTICS_FIELD_NAMES,
    AnalyticsCategory,
)
from codestrata.telemetry.analytics.installation_identity_policy import (
    COMMUNITY_ANONYMOUS_INSTALLATION_IDENTITY_POLICY_URN,
    default_installation_identity_policy,
)
from codestrata.telemetry.analytics.policy import (
    COMMUNITY_ANONYMOUS_ANALYTICS_POLICY_URN,
    COMMUNITY_ANONYMOUS_ANALYTICS_SCHEMA_URN,
    default_analytics_policy,
)
from codestrata.telemetry.analytics.repository_aggregate_policy import (
    COMMUNITY_REPOSITORY_AGGREGATE_ANALYTICS_POLICY_URN,
    default_repository_aggregate_analytics_policy,
)
from codestrata.telemetry.analytics.runtime_analytics import (
    COMMUNITY_RUNTIME_ANALYTICS_POLICY_URN,
    default_runtime_analytics_policy,
)


@dataclass(frozen=True, slots=True)
class EngineAnalyticsInventory:
    base_policy_urn: str
    base_schema_urn: str
    identity_policy_urn: str
    runtime_policy_urn: str
    assessment_policy_urn: str
    repository_policy_urn: str
    ai_policy_urn: str
    ai_schema_urn: str
    approved_categories: frozenset[str]
    approved_fields: frozenset[str]
    forbidden_fields: frozenset[str]
    ai_capabilities: frozenset[str]
    ai_provider_families: frozenset[str]
    ai_model_families: frozenset[str]
    ai_outcomes: frozenset[str]
    base_collection_enabled: bool
    base_persistence_enabled: bool
    base_transmission_enabled: bool
    base_installation_id_allowed: bool
    identity_machine_fingerprint_forbidden: bool
    runtime_transmission_enabled: bool
    assessment_transmission_enabled: bool
    repository_transmission_enabled: bool
    ai_transmission_enabled: bool
    ai_token_bucket_allowed: bool
    extras: dict[str, Any]


def load_engine_inventory() -> EngineAnalyticsInventory:
    base = default_analytics_policy()
    identity = default_installation_identity_policy()
    runtime = default_runtime_analytics_policy()
    assessment = default_assessment_analytics_policy()
    repository = default_repository_aggregate_analytics_policy()
    ai = default_ai_analytics_policy()
    return EngineAnalyticsInventory(
        base_policy_urn=COMMUNITY_ANONYMOUS_ANALYTICS_POLICY_URN,
        base_schema_urn=COMMUNITY_ANONYMOUS_ANALYTICS_SCHEMA_URN,
        identity_policy_urn=COMMUNITY_ANONYMOUS_INSTALLATION_IDENTITY_POLICY_URN,
        runtime_policy_urn=COMMUNITY_RUNTIME_ANALYTICS_POLICY_URN,
        assessment_policy_urn=COMMUNITY_ASSESSMENT_ANALYTICS_POLICY_URN,
        repository_policy_urn=COMMUNITY_REPOSITORY_AGGREGATE_ANALYTICS_POLICY_URN,
        ai_policy_urn=COMMUNITY_AI_ANALYTICS_POLICY_URN,
        ai_schema_urn=COMMUNITY_AI_ANALYTICS_SCHEMA_URN,
        approved_categories=APPROVED_ANALYTICS_CATEGORIES,
        approved_fields=APPROVED_ANALYTICS_FIELD_NAMES,
        forbidden_fields=FORBIDDEN_ANALYTICS_FIELD_NAMES,
        ai_capabilities=APPROVED_AI_CAPABILITIES,
        ai_provider_families=APPROVED_AI_PROVIDER_FAMILIES,
        ai_model_families=APPROVED_AI_MODEL_FAMILIES,
        ai_outcomes=APPROVED_AI_OUTCOMES,
        base_collection_enabled=base.collection_enabled,
        base_persistence_enabled=base.persistence_enabled,
        base_transmission_enabled=base.transmission_enabled,
        base_installation_id_allowed=base.installation_id_allowed,
        identity_machine_fingerprint_forbidden=(
            identity.machine_fingerprint_allowed is False
        ),
        runtime_transmission_enabled=runtime.transmission_enabled,
        assessment_transmission_enabled=assessment.transmission_enabled,
        repository_transmission_enabled=repository.transmission_enabled,
        ai_transmission_enabled=ai.transmission_enabled,
        ai_token_bucket_allowed=ai.token_usage_bucket_allowed,
        extras={
            "ai_usage_category": AnalyticsCategory.AI_USAGE.value,
            "vscode_usage_category": AnalyticsCategory.VSCODE_USAGE.value,
            "identity_local_persistence_allowed": identity.local_persistence_allowed,
            "identity_transmission_allowed": identity.transmission_allowed,
            "identity_analytics_collection_required": identity.analytics_collection_required,
        },
    )
