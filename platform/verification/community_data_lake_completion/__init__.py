"""Slice 8.15 Community Data Lake completion verification (Platform-only)."""

from __future__ import annotations

from verification.community_data_lake_completion.contract import (
    COMMUNITY_DATA_LAKE_COMPLETION_ID,
    COMMUNITY_DATA_LAKE_COMPLETION_VERSION,
)
from verification.community_data_lake_completion.runner import (
    run_community_data_lake_completion_verification,
)

__all__ = [
    "COMMUNITY_DATA_LAKE_COMPLETION_ID",
    "COMMUNITY_DATA_LAKE_COMPLETION_VERSION",
    "run_community_data_lake_completion_verification",
]
