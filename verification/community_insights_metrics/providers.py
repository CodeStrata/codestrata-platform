"""AI provider adoption freezes."""

from __future__ import annotations

UNAVAILABLE_EXCLUDED_FROM_SHARE = True
NOT_PROVIDER_QUALITY = True
ALLOWED_FAMILIES = frozenset(
    {"aws_bedrock", "openai", "openrouter", "unavailable"}
)
