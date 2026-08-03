"""Community Cloud AI usage policy (Slice 7.11)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.ai_usage.catalog import (
    AI_CAPABILITY_CATALOG_VERSION,
    AI_MODEL_FAMILY_CATALOG_VERSION,
    AI_PROVIDER_FAMILY_CATALOG_VERSION,
    AiCapabilityCatalog,
    AiModelFamilyCatalog,
    AiProviderFamilyCatalog,
    default_capability_catalog,
    default_model_catalog,
    default_provider_catalog,
)
from codestrata_platform.community_cloud_api.ai_usage.enums import (
    ALLOWED_AI_USAGE_CLIENTS,
    AiDataScope,
    AiDurationBucket,
    AiExecutionMode,
    AiFailureCategory,
    AiInvocationSource,
    AiOutcome,
    AiOutputUsage,
    AiProviderOwnership,
    AiTokenBucket,
    AiUsageState,
)
from codestrata_platform.community_cloud_api.assessment_metadata.enums import AssessmentHead

COMMUNITY_AI_USAGE_SCHEMA_VERSION = "1.0"
COMMUNITY_AI_USAGE_POLICY_ID = "community-ai-usage-policy"
COMMUNITY_AI_USAGE_POLICY_VERSION = "1.0"
COMMUNITY_AI_USAGE_POLICY_URN = (
    f"{COMMUNITY_AI_USAGE_POLICY_ID}:{COMMUNITY_AI_USAGE_POLICY_VERSION}"
)

FORBIDDEN_FIELD_NAMES: tuple[str, ...] = (
    "account",
    "account_id",
    "api_key",
    "bearer",
    "billing",
    "chat",
    "completion",
    "content",
    "context_text",
    "conversation",
    "cost",
    "credential",
    "deployment",
    "deployment_name",
    "documents",
    "embeddings",
    "endpoint_url",
    "error_message",
    "evidence",
    "exact_input_tokens",
    "exact_model",
    "exact_output_tokens",
    "exception",
    "exception_message",
    "file",
    "file_path",
    "finding",
    "findings",
    "generated_text",
    "graph_payload",
    "http_body",
    "input",
    "invoice",
    "mcp_server",
    "messages",
    "model_id",
    "organization",
    "output",
    "path",
    "price",
    "priority_actions",
    "prompt",
    "provider_endpoint",
    "query",
    "rag_query",
    "recommendation",
    "recommendations",
    "region",
    "repository",
    "repository_name",
    "repository_url",
    "request_body",
    "response",
    "response_body",
    "retrieved_chunks",
    "retrieved_text",
    "roadmap",
    "secret",
    "snippet",
    "source",
    "source_code",
    "stack_trace",
    "subscription",
    "system_prompt",
    "tenant",
    "token",
    "token_count",
    "tool",
    "tool_args",
    "tool_input",
    "tool_name",
    "tool_output",
    "tools",
    "user_prompt",
    "vectors",
    "workspace",
)


@dataclass(frozen=True, slots=True)
class CommunityAiUsagePolicy:
    """Deterministic privacy-first AI usage policy."""

    policy_id: str = COMMUNITY_AI_USAGE_POLICY_ID
    policy_version: str = COMMUNITY_AI_USAGE_POLICY_VERSION
    schema_version: str = COMMUNITY_AI_USAGE_SCHEMA_VERSION
    capability_catalog_version: str = AI_CAPABILITY_CATALOG_VERSION
    provider_catalog_version: str = AI_PROVIDER_FAMILY_CATALOG_VERSION
    model_catalog_version: str = AI_MODEL_FAMILY_CATALOG_VERSION
    allowed_clients: tuple[str, ...] = ALLOWED_AI_USAGE_CLIENTS
    allowed_capabilities: tuple[str, ...] = ()
    allowed_execution_modes: tuple[str, ...] = tuple(
        sorted(item.value for item in AiExecutionMode)
    )
    allowed_provider_ownership: tuple[str, ...] = tuple(
        sorted(item.value for item in AiProviderOwnership)
    )
    allowed_provider_families: tuple[str, ...] = ()
    allowed_model_families: tuple[str, ...] = ()
    allowed_outcomes: tuple[str, ...] = tuple(sorted(item.value for item in AiOutcome))
    duration_buckets: tuple[str, ...] = tuple(
        sorted(item.value for item in AiDurationBucket)
    )
    token_buckets: tuple[str, ...] = tuple(sorted(item.value for item in AiTokenBucket))
    allowed_usage_states: tuple[str, ...] = tuple(
        sorted(item.value for item in AiUsageState)
    )
    allowed_failure_categories: tuple[str, ...] = tuple(
        sorted(item.value for item in AiFailureCategory)
    )
    allowed_assessment_heads: tuple[str, ...] = tuple(
        sorted([*(item.value for item in AssessmentHead), "unavailable"])
    )
    allowed_invocation_sources: tuple[str, ...] = tuple(
        sorted(item.value for item in AiInvocationSource)
    )
    allowed_data_scopes: tuple[str, ...] = tuple(
        sorted(item.value for item in AiDataScope)
    )
    allowed_output_usage: tuple[str, ...] = tuple(
        sorted(item.value for item in AiOutputUsage)
    )
    allow_installation_id: bool = True
    require_failure_category_on_failure: bool = True
    forbid_failure_category_on_success: bool = True
    forbidden_field_names: tuple[str, ...] = FORBIDDEN_FIELD_NAMES
    limitations: tuple[str, ...] = (
        "no_production_event_store",
        "no_exactly_once_guarantee",
        "sink_and_identity_record_not_atomic",
        "unauthenticated_endpoint",
        "no_rate_limiting",
        "no_client_emitter_wiring",
        "no_prompts_or_model_responses",
        "no_exact_token_counts_or_cost",
        "no_raw_model_ids",
        "token_bucket_consistency_is_coarse",
        "community_capability_modernization_advisor_only",
        "providers_limited_to_implemented_integrations",
    )

    def __post_init__(self) -> None:
        if self.policy_id != COMMUNITY_AI_USAGE_POLICY_ID:
            raise ValueError("unsupported ai usage policy id")
        if self.policy_version != COMMUNITY_AI_USAGE_POLICY_VERSION:
            raise ValueError("unsupported ai usage policy version")
        if self.schema_version != COMMUNITY_AI_USAGE_SCHEMA_VERSION:
            raise ValueError("unsupported ai usage schema version in policy")
        capability = default_capability_catalog()
        provider = default_provider_catalog()
        model = default_model_catalog()
        if self.capability_catalog_version != capability.catalog_version:
            raise ValueError("ai capability catalog version mismatch")
        if self.provider_catalog_version != provider.catalog_version:
            raise ValueError("ai provider family catalog version mismatch")
        if self.model_catalog_version != model.catalog_version:
            raise ValueError("ai model family catalog version mismatch")
        clients = tuple(sorted(set(self.allowed_clients)))
        if not clients:
            raise ValueError("allowed clients required")
        for client in clients:
            if client not in ALLOWED_AI_USAGE_CLIENTS:
                raise ValueError(f"invalid allowed client: {client}")
        caps = tuple(self.allowed_capabilities) or capability.canonical_capabilities
        for item in caps:
            if item not in capability.canonical_capabilities:
                raise ValueError(f"invalid allowed capability: {item}")
        providers = tuple(self.allowed_provider_families) or provider.canonical_families
        for item in providers:
            if item not in provider.canonical_families:
                raise ValueError(f"invalid allowed provider family: {item}")
        models = tuple(self.allowed_model_families) or model.canonical_families
        for item in models:
            if item not in model.canonical_families:
                raise ValueError(f"invalid allowed model family: {item}")
        object.__setattr__(self, "allowed_clients", clients)
        object.__setattr__(self, "allowed_capabilities", tuple(sorted(caps)))
        object.__setattr__(self, "allowed_provider_families", tuple(sorted(providers)))
        object.__setattr__(self, "allowed_model_families", tuple(sorted(models)))
        object.__setattr__(
            self, "forbidden_field_names", tuple(sorted(set(self.forbidden_field_names)))
        )
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def capability_catalog(self) -> AiCapabilityCatalog:
        return AiCapabilityCatalog(canonical_capabilities=self.allowed_capabilities)

    def provider_catalog(self) -> AiProviderFamilyCatalog:
        return AiProviderFamilyCatalog(canonical_families=self.allowed_provider_families)

    def model_catalog(self) -> AiModelFamilyCatalog:
        return AiModelFamilyCatalog(canonical_families=self.allowed_model_families)

    @classmethod
    def default(cls) -> CommunityAiUsagePolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "allow_installation_id": self.allow_installation_id,
            "allowed_assessment_heads": list(self.allowed_assessment_heads),
            "allowed_capabilities": list(self.allowed_capabilities),
            "allowed_clients": list(self.allowed_clients),
            "allowed_data_scopes": list(self.allowed_data_scopes),
            "allowed_execution_modes": list(self.allowed_execution_modes),
            "allowed_failure_categories": list(self.allowed_failure_categories),
            "allowed_invocation_sources": list(self.allowed_invocation_sources),
            "allowed_model_families": list(self.allowed_model_families),
            "allowed_outcomes": list(self.allowed_outcomes),
            "allowed_output_usage": list(self.allowed_output_usage),
            "allowed_provider_families": list(self.allowed_provider_families),
            "allowed_provider_ownership": list(self.allowed_provider_ownership),
            "allowed_usage_states": list(self.allowed_usage_states),
            "capability_catalog_version": self.capability_catalog_version,
            "duration_buckets": list(self.duration_buckets),
            "forbid_failure_category_on_success": self.forbid_failure_category_on_success,
            "forbidden_field_names": list(self.forbidden_field_names),
            "limitations": list(self.limitations),
            "model_catalog_version": self.model_catalog_version,
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "provider_catalog_version": self.provider_catalog_version,
            "require_failure_category_on_failure": self.require_failure_category_on_failure,
            "schema_version": self.schema_version,
            "token_buckets": list(self.token_buckets),
        }


def default_ai_usage_policy() -> CommunityAiUsagePolicy:
    return CommunityAiUsagePolicy.default()
