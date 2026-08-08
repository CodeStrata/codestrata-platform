"""Optional cache — Slice 15.7 ships with no-cache posture."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights.policy import CACHE_MODE


def cache_enabled() -> bool:
    return CACHE_MODE != "none"


def cache_posture() -> dict[str, object]:
    return {"mode": CACHE_MODE, "ttl_seconds": None, "backend": None}
