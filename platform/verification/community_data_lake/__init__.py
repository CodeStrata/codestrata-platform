"""SV.9 Community Data Lake integration verification (Platform-only)."""

from __future__ import annotations

from verification.community_data_lake.contract import (
    COMMUNITY_DATA_LAKE_VERIFICATION_ID,
    COMMUNITY_DATA_LAKE_VERIFICATION_VERSION,
)
from verification.community_data_lake.runner import run_community_data_lake_verification

__all__ = [
    "COMMUNITY_DATA_LAKE_VERIFICATION_ID",
    "COMMUNITY_DATA_LAKE_VERIFICATION_VERSION",
    "run_community_data_lake_verification",
]
