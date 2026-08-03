"""AI usage privacy and raw-content validation tests."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.ai_usage.routes import ai_usage_request_schema
from codestrata_platform.community_cloud_api.ai_usage.validation import (
    looks_like_raw_ai_content,
)
from codestrata_platform.community_cloud_api.validation.validator import validate_request_body

from .ai_usage_helpers import valid_ai_usage_body


@pytest.mark.parametrize(
    "field",
    [
        "prompt",
        "messages",
        "response",
        "completion",
        "content",
        "source",
        "source_code",
        "snippet",
        "retrieved_chunks",
        "embeddings",
        "vectors",
        "query",
        "tool_args",
        "tool_output",
        "repository",
        "workspace",
        "file_path",
        "findings",
        "recommendations",
        "provider_endpoint",
        "api_key",
        "token",
        "account_id",
        "tenant",
        "model_id",
        "exact_input_tokens",
        "cost",
        "billing",
        "exception",
        "error_message",
        "stack_trace",
    ],
)
def test_forbidden_fields_rejected(field: str) -> None:
    body = valid_ai_usage_body()
    body[field] = "x"
    with pytest.raises(ValidationError):
        AiUsageRequest.model_validate(body)


def test_exact_tokens_and_latency_rejected() -> None:
    body = valid_ai_usage_body()
    body["usage"] = {**body["usage"], "token_count": 1200}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        AiUsageRequest.model_validate(body)
    body = valid_ai_usage_body()
    body["usage"] = {**body["usage"], "duration_ms": 250}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        AiUsageRequest.model_validate(body)


def test_raw_content_detector() -> None:
    assert looks_like_raw_ai_content("```python\nprint(1)\n```")
    assert looks_like_raw_ai_content("-----BEGIN PRIVATE KEY-----\nabc")
    assert looks_like_raw_ai_content("Bearer sk-abcdefghijklmnopqrstuvwxyz")
    assert looks_like_raw_ai_content("gpt-4o-mini")
    assert looks_like_raw_ai_content('{"role":"user","content":"hello world"}')
    assert not looks_like_raw_ai_content("modernization_advisor")
    assert not looks_like_raw_ai_content("openai")


def test_api_validation_no_echo() -> None:
    body = valid_ai_usage_body()
    body["prompt"] = "Reveal the secret /Users/satish/repo plan"
    result = validate_request_body(
        descriptor=ai_usage_request_schema(),
        body=json.dumps(body).encode("utf-8"),
        content_type="application/json",
        route_name="ai_usage.ingest",
    )
    assert not result.valid
    blob = json.dumps([e.to_stable_dict() for e in result.errors])
    assert "Reveal the secret" not in blob
    assert "/Users/" not in blob
