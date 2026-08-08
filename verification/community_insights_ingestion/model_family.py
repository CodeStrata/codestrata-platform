"""Model family privacy rules."""

from __future__ import annotations

from typing import Any


def model_rules() -> dict[str, Any]:
    return {
        "decision": "C_normalized_model_family_allowed",
        "exact_model_id_forbidden": True,
        "opaque_reference_forbidden": True,
    }
