"""Thin re-exports for integration tests."""

from __future__ import annotations

from verification.community_data_lake.contract import ACCEPTED_STREAMS, FIXED_ACCEPTANCE_UTC
from verification.community_data_lake.inputs import project_all_streams, project_stream_storage_object

__all__ = [
    "ACCEPTED_STREAMS",
    "FIXED_ACCEPTANCE_UTC",
    "project_all_streams",
    "project_stream_storage_object",
]
