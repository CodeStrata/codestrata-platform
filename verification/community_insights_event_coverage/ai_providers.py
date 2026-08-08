"""AI provider coverage helpers."""

from __future__ import annotations

from typing import Any


def provider_rules() -> dict[str, Any]:
    return {
        "field": "payload.usage.provider_family",
        "canonical_today": ["aws_bedrock", "openai", "openrouter", "unavailable"],
        "bedrock_alias": "aws_bedrock",
        "openrouter_present": True,
        "credentials_forbidden": True,
        "future_change": "CR-15.3-002",
    }
