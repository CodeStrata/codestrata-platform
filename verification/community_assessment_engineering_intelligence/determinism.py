"""Deterministic serialization helpers for Slice 17.19."""

from __future__ import annotations

import copy
import json
import re
from typing import Any

from verification.community_assessment_engineering_intelligence.helpers import (
    report_text_is_safe,
)

_VOLATILE_SUMMARY_KEYS = frozenset(
    {
        "portfolio_run_id",
        "assessment_run_id",
        "bytes",
        "manifest_bytes",
        "heads_bytes",
        "probe_duration_seconds",
        "current_path",
    }
)

_COUNT_DETAIL = re.compile(r"bytes=|count=|run_id=|matches=", re.IGNORECASE)


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def strip_volatile_fields(payload: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(payload)
    for section_key, section in list(out.items()):
        if isinstance(section, dict):
            for vk in _VOLATILE_SUMMARY_KEYS:
                if vk in section:
                    section[vk] = "<volatile>"
            # Nested selected rows may include run ids / paths
            if "selected" in section and isinstance(section["selected"], list):
                for row in section["selected"]:
                    if isinstance(row, dict):
                        for vk in ("current_path", "assessment_run_id"):
                            if vk in row:
                                row[vk] = "<volatile>"
            if "coverage" in section and isinstance(section["coverage"], list):
                for row in section["coverage"]:
                    if isinstance(row, dict) and "assessment_run_id" in row:
                        row["assessment_run_id"] = "<volatile>"
            if section_key in {"eir_generation", "membership"}:
                if "portfolio_run_id" in section:
                    section["portfolio_run_id"] = "<volatile>"
        if section_key == "checks" and isinstance(section, list):
            for item in section:
                if not isinstance(item, dict):
                    continue
                detail = str(item.get("detail", ""))
                if _COUNT_DETAIL.search(detail):
                    item["detail"] = "<volatile>"
                cid = str(item.get("check_id", ""))
                if cid.startswith("membership:") or cid.startswith("eir_generation:"):
                    if "repos=" in detail or "a=" in detail:
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
