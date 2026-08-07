"""Production fail-closed re-export (Slice 12.4)."""

from __future__ import annotations

from verification.community_client_boundary_cleanup.quarantine import (
    check_production_fail_closed,
)

__all__ = ["check_production_fail_closed"]
