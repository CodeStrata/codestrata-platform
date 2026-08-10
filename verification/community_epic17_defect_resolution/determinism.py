"""Determinism helpers for Slice 17.22."""

from __future__ import annotations

from typing import Any

from verification.community_epic17_defect_resolution.helpers import dict_to_canonical_json


def assert_deterministic_payload(payload: dict[str, Any]) -> None:
    text = dict_to_canonical_json(payload)
    assert "timestamp" not in text
    assert "/Users/" not in text
