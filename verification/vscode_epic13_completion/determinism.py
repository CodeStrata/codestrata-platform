"""Determinism helpers for Slice 13.15."""

from __future__ import annotations

from typing import Any

from verification.vscode_epic13_completion.safety import dict_to_canonical_json


def reports_byte_identical(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return dict_to_canonical_json(a) == dict_to_canonical_json(b)
