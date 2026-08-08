"""Validation dataset external source helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_event_coverage.inventory import exists, load_json


def validation_dataset_source(monorepo: Path) -> dict[str, Any]:
    rel = "validation/repository-catalog/catalog.json"
    catalog = load_json(monorepo, rel)
    return {
        "classification": "external_metric_source",
        "path": rel,
        "present": exists(monorepo, rel),
        "schema_name": catalog.get("schema_name"),
        "force_into_telemetry": False,
    }
