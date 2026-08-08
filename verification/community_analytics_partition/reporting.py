"""Report writer for Slice 15.2."""

from __future__ import annotations

from pathlib import Path

from verification.community_analytics_partition.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV152_OUTPUT_RELATIVE,
)
from verification.community_analytics_partition.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_analytics_partition.models import (
    CommunityAnalyticsPartitionReport,
)


def write_report(
    monorepo: Path, report: CommunityAnalyticsPartitionReport
) -> Path:
    out_dir = monorepo / SV152_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    assert safe, f"unsafe report content: {reason}"
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Partition redesign required: **{report.partition_redesign_required}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 15.2 validates that the Slice 15.1 Hive partition strategy "
        "supports privacy-safe, bounded Community Insights analytics. "
        "No additive path dimensions. Slice 15.7 not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
