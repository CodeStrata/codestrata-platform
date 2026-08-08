"""Synthetic object-count fixtures (no real S3)."""

from __future__ import annotations

from typing import Any

FIXTURES: dict[str, dict[str, Any]] = {
    "tiny": {"objects": 10, "avg_bytes": 2048, "within_budget": True},
    "product_discovery": {"objects": 500, "avg_bytes": 8192, "within_budget": True},
    "near_limit": {"objects": 2000, "avg_bytes": 50000, "within_budget": True},
    "over_object_limit": {"objects": 2500, "avg_bytes": 4096, "within_budget": False},
    "over_byte_limit": {"objects": 1500, "avg_bytes": 80000, "within_budget": False},
    "multi_stream_30_day": {"objects": 1800, "avg_bytes": 10000, "within_budget": True},
    "lifetime_365": {"objects": 5000, "avg_bytes": 20000, "within_budget": False},
}


def fixture_within_budgets(name: str, *, max_objects: int, max_bytes: int) -> bool:
    f = FIXTURES[name]
    total_bytes = int(f["objects"]) * int(f["avg_bytes"])
    return int(f["objects"]) <= max_objects and total_bytes <= max_bytes
