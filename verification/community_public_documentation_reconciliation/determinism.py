"""Determinism helpers for Slice 17.26."""

from __future__ import annotations

from typing import Any

from verification.community_public_documentation_reconciliation.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)


def reports_byte_identical(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return dict_to_canonical_json(a) == dict_to_canonical_json(b)


def assert_deterministic_payload(payload: dict[str, Any]) -> None:
    text = dict_to_canonical_json(payload)
    assert "timestamp" not in text
    assert "/Users/" not in text
    assert report_text_is_safe(text)
