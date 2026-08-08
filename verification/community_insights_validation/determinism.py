"""Determinism helpers."""

from __future__ import annotations

import json
from typing import Any

from verification.community_insights_validation.fixtures import (
    POISON_CREDENTIAL,
    POISON_INSTALLATION,
    POISON_MODEL,
    POISON_PROMPT,
    POISON_S3,
)


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def reports_byte_identical(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return dict_to_canonical_json(a) == dict_to_canonical_json(b)


def report_text_is_safe(text: str) -> tuple[bool, str]:
    lowered = text.lower()
    for needle, reason in (
        ("/users/", "path_leak"),
        ("/home/", "path_leak"),
        ("file://", "path_leak"),
        ("timestamp", "timestamp"),
        ("sk-live", "secret"),
        ("test-only-insights-password", "password_leak"),
        ("test-only-session-signing-secret", "session_secret_leak"),
        (POISON_INSTALLATION.lower(), "installation_leak"),
        (POISON_MODEL.lower(), "model_leak"),
        (POISON_S3.lower(), "s3_leak"),
        (POISON_PROMPT.lower(), "prompt_leak"),
        (POISON_CREDENTIAL.lower(), "credential_leak"),
    ):
        if needle in lowered:
            return False, reason
    return True, "safe"
