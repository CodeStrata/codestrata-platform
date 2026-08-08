"""Report writer for Slice 15.1."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_audit.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV151_OUTPUT_RELATIVE,
)
from verification.community_data_lake_audit.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_data_lake_audit.models import CommunityDataLakeAuditReport


def write_report(monorepo: Path, report: CommunityDataLakeAuditReport) -> Path:
    out_dir = monorepo / SV151_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    assert safe, f"unsafe report content: {reason}"
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 15.1 audits the Community Data Lake architecture and freezes "
        "`community-data-lake-policy:1.0` for future Community Insights work.\n\n"
        "Does not redesign telemetry/schemas. Does not build dashboards, "
        "aggregations, or APIs. Slice 15.7 not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
