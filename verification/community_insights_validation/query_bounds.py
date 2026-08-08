"""Bounded S3 query checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check, ensure_platform_importable
from verification.community_insights_validation.fixtures import bounded_reader
from verification.community_insights_validation.models import CheckResult, Defect


def check_query_bounds(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights_storage.reader import (
        reject_arbitrary_prefix,
    )

    forbidden = ("raw/", "quarantine/", "caller/")
    for prefix in forbidden:
        try:
            reject_arbitrary_prefix(prefix)
            ok = False
        except Exception:
            ok = True
        add_check(
            checks,
            defects,
            f"query:reject_{prefix.rstrip('/')}",
            ok,
            "rejected",
            "query_bounds",
        )

    reader, _fx = bounded_reader(monorepo)
    add_check(
        checks,
        defects,
        "query:bounded_reader_ready",
        reader is not None,
        "ready",
        "query_bounds",
    )
    return checks, defects
