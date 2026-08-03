"""AI usage model and catalog tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.ai_usage.catalog import (
    AI_CAPABILITY_CATALOG_URN,
    AI_MODEL_FAMILY_CATALOG_URN,
    AI_PROVIDER_FAMILY_CATALOG_URN,
    AiCapabilityCatalog,
    AiModelFamilyCatalog,
    AiProviderFamilyCatalog,
)
from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.ai_usage.policy import (
    COMMUNITY_AI_USAGE_POLICY_URN,
    CommunityAiUsagePolicy,
)

from .ai_usage_helpers import valid_ai_usage_body


def test_required_fields_and_catalogs() -> None:
    model = AiUsageRequest.model_validate(valid_ai_usage_body())
    assert model.usage.capability == "modernization_advisor"
    assert model.usage.provider_family == "openai"
    assert model.usage.model_family == "gpt_family"
    assert AiCapabilityCatalog.default().catalog_token == AI_CAPABILITY_CATALOG_URN
    assert AiProviderFamilyCatalog.default().catalog_token == AI_PROVIDER_FAMILY_CATALOG_URN
    assert AiModelFamilyCatalog.default().catalog_token == AI_MODEL_FAMILY_CATALOG_URN
    assert CommunityAiUsagePolicy.default().policy_token == COMMUNITY_AI_USAGE_POLICY_URN


def test_aliases_and_unsupported_rejected() -> None:
    body = valid_ai_usage_body()
    body["usage"] = {**body["usage"], "provider_family": "bedrock"}  # type: ignore[dict-item]
    assert (
        AiUsageRequest.model_validate(body).usage.provider_family == "aws_bedrock"
    )
    body = valid_ai_usage_body()
    body["usage"] = {**body["usage"], "capability": "code_assistance"}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        AiUsageRequest.model_validate(body)
    body = valid_ai_usage_body()
    body["usage"] = {**body["usage"], "provider_family": "anthropic"}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        AiUsageRequest.model_validate(body)
    body = valid_ai_usage_body()
    body["usage"] = {**body["usage"], "model_family": "gpt-4o-mini"}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        AiUsageRequest.model_validate(body)


def test_failure_and_token_rules() -> None:
    body = valid_ai_usage_body()
    usage = dict(body["usage"])  # type: ignore[arg-type]
    usage["outcome"] = "failed"
    usage.pop("failure_category", None)
    body["usage"] = usage
    with pytest.raises(ValidationError):
        AiUsageRequest.model_validate(body)
    usage["failure_category"] = "provider_unavailable"
    body["usage"] = usage
    AiUsageRequest.model_validate(body)

    bad_tokens = valid_ai_usage_body()
    bad_tokens["usage"] = {
        **bad_tokens["usage"],  # type: ignore[dict-item]
        "input_token_bucket": "1k_to_4k",
        "output_token_bucket": "1_to_1k",
        "total_token_bucket": "none",
    }
    with pytest.raises(ValidationError):
        AiUsageRequest.model_validate(bad_tokens)


def test_unsupported_client_and_policy() -> None:
    body = valid_ai_usage_body()
    body["client"] = {"name": "other_extension", "version": "0.2.0", "platform": "darwin"}
    with pytest.raises(ValidationError):
        AiUsageRequest.model_validate(body)
    with pytest.raises(ValueError):
        CommunityAiUsagePolicy(policy_version="9.9")
