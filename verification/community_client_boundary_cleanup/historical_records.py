"""Historical records re-export (Slice 12.4)."""

from __future__ import annotations

from verification.community_client_boundary_cleanup.envelope_compatibility import (
    check_envelope_compatibility as check_historical_records,
)

__all__ = ["check_historical_records"]
