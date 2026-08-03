"""Strict AI usage request models (Slice 7.11)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, StrictBool, StrictStr, field_validator, model_validator

from codestrata_platform.community_cloud_api.ai_usage.enums import (
    ALLOWED_AI_USAGE_CLIENTS,
    TOKEN_BUCKET_RANK,
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
from codestrata_platform.community_cloud_api.ai_usage.policy import (
    COMMUNITY_AI_USAGE_SCHEMA_VERSION,
    default_ai_usage_policy,
)
from codestrata_platform.community_cloud_api.validation.models import (
    CommunityApiRequestModel,
)
from codestrata_platform.community_cloud_api.validation.schema import (
    ApiClientVersion,
    ApiEventId,
    ApiInstallationId,
    ApiPlatformName,
)


class AiUsageClient(CommunityApiRequestModel):
    """Supported CodeStrata clients only."""

    name: StrictStr = Field(min_length=1, max_length=64)
    version: ApiClientVersion
    platform: ApiPlatformName

    @field_validator("name")
    @classmethod
    def _client(cls, value: str) -> str:
        text = value.strip()
        if text not in ALLOWED_AI_USAGE_CLIENTS:
            raise ValueError("invalid_enum")
        return text


class AiUsageContext(CommunityApiRequestModel):
    """Bounded anonymous AI usage context — no source content."""

    assessment_head: StrictStr = Field(min_length=1, max_length=64)
    invocation_source: StrictStr = Field(min_length=1, max_length=32)
    offline_mode: StrictBool
    user_initiated: StrictBool
    data_scope: StrictStr = Field(min_length=1, max_length=64)
    output_usage: StrictStr = Field(min_length=1, max_length=64)

    @field_validator("assessment_head")
    @classmethod
    def _head(cls, value: str) -> str:
        text = value.strip()
        policy = default_ai_usage_policy()
        if text not in policy.allowed_assessment_heads:
            raise ValueError("invalid_enum")
        return text

    @field_validator("invocation_source")
    @classmethod
    def _source(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AiInvocationSource}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("data_scope")
    @classmethod
    def _scope(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AiDataScope}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("output_usage")
    @classmethod
    def _output(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AiOutputUsage}:
            raise ValueError("invalid_enum")
        return text


class AiUsage(CommunityApiRequestModel):
    """Bounded AI operational classification — no prompts or exact tokens."""

    capability: StrictStr = Field(min_length=1, max_length=64)
    execution_mode: StrictStr = Field(min_length=1, max_length=32)
    provider_ownership: StrictStr = Field(min_length=1, max_length=32)
    provider_family: StrictStr = Field(min_length=1, max_length=32)
    model_family: StrictStr = Field(min_length=1, max_length=32)
    outcome: StrictStr = Field(min_length=1, max_length=32)
    duration_bucket: StrictStr = Field(min_length=1, max_length=32)
    input_token_bucket: StrictStr = Field(min_length=1, max_length=32)
    output_token_bucket: StrictStr = Field(min_length=1, max_length=32)
    total_token_bucket: StrictStr = Field(min_length=1, max_length=32)
    tool_usage: StrictStr = Field(min_length=1, max_length=32)
    rag_usage: StrictStr = Field(min_length=1, max_length=32)
    graph_usage: StrictStr = Field(min_length=1, max_length=32)
    failure_category: StrictStr | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("capability")
    @classmethod
    def _capability(cls, value: str) -> str:
        policy = default_ai_usage_policy()
        canonical = policy.capability_catalog().canonicalize(value.strip())
        if canonical is None or canonical not in policy.allowed_capabilities:
            raise ValueError("invalid_enum")
        return canonical

    @field_validator("execution_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AiExecutionMode}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("provider_ownership")
    @classmethod
    def _ownership(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AiProviderOwnership}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("provider_family")
    @classmethod
    def _provider(cls, value: str) -> str:
        policy = default_ai_usage_policy()
        canonical = policy.provider_catalog().canonicalize(value.strip())
        if canonical is None or canonical not in policy.allowed_provider_families:
            raise ValueError("invalid_enum")
        return canonical

    @field_validator("model_family")
    @classmethod
    def _model(cls, value: str) -> str:
        policy = default_ai_usage_policy()
        canonical = policy.model_catalog().canonicalize(value.strip())
        if canonical is None or canonical not in policy.allowed_model_families:
            raise ValueError("invalid_enum")
        return canonical

    @field_validator("outcome")
    @classmethod
    def _outcome(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AiOutcome}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("duration_bucket")
    @classmethod
    def _duration(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AiDurationBucket}:
            raise ValueError("invalid_enum")
        return text

    @field_validator(
        "input_token_bucket", "output_token_bucket", "total_token_bucket"
    )
    @classmethod
    def _token(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AiTokenBucket}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("tool_usage", "rag_usage", "graph_usage")
    @classmethod
    def _usage_state(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AiUsageState}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("failure_category")
    @classmethod
    def _failure(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if text not in {item.value for item in AiFailureCategory}:
            raise ValueError("invalid_enum")
        return text

    @model_validator(mode="after")
    def _semantic_rules(self) -> AiUsage:
        policy = default_ai_usage_policy()
        successish = self.outcome == AiOutcome.SUCCEEDED.value
        failedish = self.outcome == AiOutcome.FAILED.value
        if (
            policy.require_failure_category_on_failure
            and failedish
            and self.failure_category is None
        ):
            raise ValueError("missing")
        if (
            policy.forbid_failure_category_on_success
            and successish
            and self.failure_category is not None
        ):
            raise ValueError("invalid_enum")

        # Coarse token consistency: total cannot be none when input/output show usage.
        input_rank = TOKEN_BUCKET_RANK.get(self.input_token_bucket)
        output_rank = TOKEN_BUCKET_RANK.get(self.output_token_bucket)
        total_rank = TOKEN_BUCKET_RANK.get(self.total_token_bucket)
        if (
            self.total_token_bucket == AiTokenBucket.NONE.value
            and (
                (input_rank is not None and input_rank > 0)
                or (output_rank is not None and output_rank > 0)
            )
        ):
            raise ValueError("invalid_enum")
        # If all three are concrete ranks, total should not be below either side.
        if (
            input_rank is not None
            and output_rank is not None
            and total_rank is not None
            and self.input_token_bucket != AiTokenBucket.UNAVAILABLE.value
            and self.output_token_bucket != AiTokenBucket.UNAVAILABLE.value
            and self.total_token_bucket != AiTokenBucket.UNAVAILABLE.value
            and total_rank < max(input_rank, output_rank)
        ):
            raise ValueError("invalid_enum")
        return self


class AiUsageRequest(CommunityApiRequestModel):
    """Privacy-first AI usage envelope."""

    schema_version: Literal["1.0"]  # type: ignore[valid-type]
    event_id: ApiEventId
    client: AiUsageClient
    installation_id: ApiInstallationId | None = None
    usage: AiUsage
    context: AiUsageContext

    def fingerprint_payload(self) -> dict[str, Any]:
        return self.to_stable_dict()

    def schema_version_value(self) -> str:
        return COMMUNITY_AI_USAGE_SCHEMA_VERSION
