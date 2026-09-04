"""Fail-closed payload sanitization for portable evidence artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from codestrata.domain.evidence.framework.models import SensitivityPolicy
from codestrata.security.redaction import redact_report_payload

_SOURCE_TEXT_KEYS = frozenset(
    {
        "content",
        "excerpt",
        "raw_content",
        "snippet",
        "source_code",
        "source_text",
    }
)
_NOT_STORED = "[not stored by evidence policy]"


def _remove_source_text(value: Any, *, key: str | None = None) -> Any:
    if isinstance(value, Mapping):
        return {
            str(child_key): _remove_source_text(child_value, key=str(child_key))
            for child_key, child_value in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_remove_source_text(item, key=key) for item in value]
    if key and (key.lower() in _SOURCE_TEXT_KEYS or key.lower().endswith("_snippet")):
        return None if value is None else _NOT_STORED
    return value


def sanitize_evidence_payload(
    payload: Mapping[str, Any],
    policy: SensitivityPolicy,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Return a detached payload plus an audit list of applied protections."""

    sanitized: dict[str, Any] = dict(payload)
    redactions: list[str] = []
    if policy.redact_secrets:
        redacted = redact_report_payload(sanitized)
        if redacted != sanitized:
            redactions.append("recognized secret patterns redacted")
        sanitized = redacted
    if not policy.store_source_snippets:
        without_source = _remove_source_text(sanitized)
        assert isinstance(without_source, dict)
        if without_source != sanitized:
            redactions.append("source snippets not stored")
        sanitized = without_source
    return sanitized, tuple(redactions)
