"""Partition compatibility re-export (Slice 12.4)."""

from __future__ import annotations

from verification.community_client_boundary_cleanup.envelope_compatibility import (
    check_partition_compatibility,
)

__all__ = ["check_partition_compatibility"]
