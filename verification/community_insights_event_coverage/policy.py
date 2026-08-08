"""Policy loader helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_event_coverage.contract import POLICY_RELATIVE
from verification.community_insights_event_coverage.inventory import load_json


def load_coverage_policy(monorepo: Path) -> dict[str, Any]:
    return load_json(monorepo, POLICY_RELATIVE)
