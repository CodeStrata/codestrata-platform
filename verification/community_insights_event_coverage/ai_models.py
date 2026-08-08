"""AI model privacy decision helpers."""

from __future__ import annotations

from typing import Any


def model_privacy_decision() -> dict[str, Any]:
    """Outcome C: normalized model family allowed; exact model id forbidden."""
    return {
        "outcome": "C",
        "decision": "C_normalized_model_family_allowed",
        "allowed_field": "payload.usage.model_family",
        "exact_model_id_permitted": False,
        "privacy_wins_over_dashboard": True,
    }
