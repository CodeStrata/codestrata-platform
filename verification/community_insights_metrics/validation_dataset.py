"""Validation dataset growth freezes."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_metrics.inventory import load_json

EXTERNAL = True
NOT_TELEMETRY = True
GIT_TIMESTAMPS_NOT_APPROVED = True
VALIDATION_CATALOG_RELATIVE = "validation/repository-catalog/catalog.json"


def validation_catalog_size(monorepo: Path) -> int | None:
    data = load_json(monorepo, VALIDATION_CATALOG_RELATIVE)
    if not data:
        return None
    repos = data.get("repositories")
    if isinstance(repos, list):
        return len(repos)
    fixtures = data.get("fixtures")
    if isinstance(fixtures, list):
        return len(fixtures)
    return None


def validation_has_history_snapshots(monorepo: Path) -> bool:
    data = load_json(monorepo, VALIDATION_CATALOG_RELATIVE)
    if not data:
        return False
    history = data.get("history") or data.get("snapshots") or data.get("growth")
    return bool(history)
