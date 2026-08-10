"""Deterministic serialization helpers for Slice 17.18."""

from __future__ import annotations

import copy
import json
import re
from typing import Any

from verification.community_data_lake_insights.helpers import report_text_is_safe

_VOLATILE_SUMMARY_KEYS = frozenset(
    {
        "before_counts",
        "after_counts",
        "deltas",
        "quarantine_before",
        "quarantine_after",
        "quarantine_delta",
        "report_artifacts_before",
        "report_artifacts_after",
        "report_artifacts_delta",
        "probe_duration_seconds",
        "live_probe_duration_seconds",
        "object_count_class",
        "total_raw_objects",
        "total_objects",
        "event_ids_posted",
        "post_statuses",
        "payload_flags",
        "overview_metric_values",
        "dashboard_metric_values",
        "aggregation_duration_seconds",
        "list_request_count",
    }
)

_COUNT_DETAIL = re.compile(r"count=", re.IGNORECASE)


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def strip_volatile_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize live-volatile fields for dual-run determinism comparison."""

    out = copy.deepcopy(payload)
    for section_key, section in list(out.items()):
        if isinstance(section, dict):
            for vk in _VOLATILE_SUMMARY_KEYS:
                if vk in section:
                    section[vk] = "<volatile>"
            # Nested live count maps
            for nested in ("before_counts", "after_counts", "deltas"):
                if nested in section and isinstance(section[nested], dict):
                    section[nested] = {k: "<volatile>" for k in sorted(section[nested])}
        if section_key == "checks" and isinstance(section, list):
            for item in section:
                if not isinstance(item, dict):
                    continue
                detail = str(item.get("detail", ""))
                if _COUNT_DETAIL.search(detail) or "delta=" in detail.lower():
                    item["detail"] = "<volatile>"
                cid = str(item.get("check_id", ""))
                if cid.startswith("live_probe:") or cid.startswith("dashboard:live"):
                    if "status=" in detail or "duration=" in detail:
                        item["detail"] = "<volatile>"
    return out


def canonical_for_determinism(payload: dict[str, Any]) -> str:
    return dict_to_canonical_json(strip_volatile_fields(payload))


__all__ = [
    "canonical_for_determinism",
    "dict_to_canonical_json",
    "report_text_is_safe",
    "strip_volatile_fields",
]
