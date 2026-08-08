"""Checkpoint posture for Slice 15.7 — retention-only, no derived S3 state."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights.policy import CHECKPOINT_MODE

CHECKPOINT_ENABLED = False
DERIVED_PREFIX = None  # intentionally unset — no derived/insights/ without policy update


def checkpoint_posture() -> dict[str, object]:
    return {
        "mode": CHECKPOINT_MODE,
        "checkpoint_enabled": CHECKPOINT_ENABLED,
        "derived_prefix": DERIVED_PREFIX,
        "limitation": "first_repeat_retention_only",
    }
