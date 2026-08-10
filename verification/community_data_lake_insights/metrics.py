"""Aggregation metrics register / SUPPORTED_METRICS overlap."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_insights.contract import AGG_REGISTER, EXPECTED_SECTIONS
from verification.community_data_lake_insights.helpers import check, load_json
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_metrics(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    register = load_json(monorepo / AGG_REGISTER)
    entries = [e for e in (register.get("entries") or []) if isinstance(e, dict)]
    sections = {e.get("section") for e in entries}
    metric_ids = {e.get("metric_id") for e in entries}

    for section in EXPECTED_SECTIONS:
        ok = section in sections
        checks.append(check(f"metrics:section_{section}", ok, section, "metrics"))
        if not ok:
            defects.append(
                Defect("missing_section", f"metrics:section_{section}", section, "absent")
            )

    supported: set[str] = set()
    try:
        from codestrata_platform.community_cloud_api.insights.policy import (
            SUPPORTED_METRICS,
        )

        supported = set(SUPPORTED_METRICS)
    except Exception:  # noqa: BLE001
        supported = set()

    if supported:
        # Every SUPPORTED_METRICS id should appear in the aggregation register.
        overlap_ok = supported.issubset(metric_ids)
        checks.append(
            check(
                "metrics:supported_metrics_overlap",
                overlap_ok,
                f"supported={len(supported)} register={len(metric_ids)}",
                "metrics",
            )
        )
        if not overlap_ok:
            missing = sorted(supported - metric_ids)
            defects.append(
                Defect(
                    "supported_metrics_gap",
                    "metrics:supported_metrics_overlap",
                    "all supported in register",
                    f"missing_count={len(missing)}",
                )
            )
    else:
        checks.append(
            check(
                "metrics:supported_metrics_overlap",
                False,
                "SUPPORTED_METRICS import failed",
                "metrics",
            )
        )
        defects.append(
            Defect(
                "supported_metrics_import",
                "metrics:supported_metrics_overlap",
                "importable",
                "failed",
            )
        )

    summary = {
        "sections": sorted(s for s in sections if s),
        "metric_count": len(metric_ids),
        "supported_count": len(supported),
        "reader": register.get("reader"),
        "source": register.get("source"),
    }
    return checks, defects, summary
