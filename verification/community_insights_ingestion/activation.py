"""Operational activation."""

from __future__ import annotations

from verification.community_insights_ingestion.contract import ACTIVATION_STATE


def activation_state() -> str:
    return ACTIVATION_STATE
