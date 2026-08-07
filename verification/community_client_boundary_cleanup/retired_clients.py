"""Retired-client policy checks (Slice 12.4)."""

from __future__ import annotations

from pathlib import Path

from verification.community_client_boundary_cleanup.active_clients import check_retired_clients
from verification.community_client_boundary_cleanup.models import CheckResult, Defect

__all__ = ["check_retired_clients"]


def check_retired_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    return check_retired_clients(monorepo)
