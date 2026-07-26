"""Outbound safety checks before sending repository content to AI providers."""

from __future__ import annotations

import re
from collections.abc import Sequence

from codestrata.security.database_url import redact_database_url
from codestrata_platform.rag.domain.retrieval import RetrievalHit

_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)bearer\s+[a-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)aws_secret_access_key\s*=\s*\S+"),
)


def scrub_text(text: str) -> str:
    """Redact obvious secrets from outbound repository evidence text."""

    scrubbed = redact_database_url(text)
    for pattern in _SECRET_PATTERNS:
        scrubbed = pattern.sub("[REDACTED]", scrubbed)
    return scrubbed


def scrub_hits(hits: Sequence[RetrievalHit]) -> tuple[RetrievalHit, ...]:
    """Return hits with content scrubbed for outbound provider calls."""

    cleaned: list[RetrievalHit] = []
    for hit in hits:
        content = hit.content
        if content:
            content = scrub_text(content)
        cleaned.append(hit.model_copy(update={"content": content}))
    return tuple(cleaned)


def looks_like_instruction_injection(text: str) -> bool:
    """Heuristic flag for prompt-injection style evidence (diagnostic only)."""

    lowered = text.lower()
    markers = (
        "ignore previous instructions",
        "disregard the system prompt",
        "you are now",
        "system:",
        "developer message",
    )
    return any(marker in lowered for marker in markers)
