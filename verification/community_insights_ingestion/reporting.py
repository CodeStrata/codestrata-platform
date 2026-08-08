"""Report writer for Slice 15.4."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_ingestion.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV154_OUTPUT_RELATIVE,
)
from verification.community_insights_ingestion.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_insights_ingestion.models import (
    CommunityInsightsIngestionReport,
)


def write_report(
    monorepo: Path, report: CommunityInsightsIngestionReport
) -> Path:
    out_dir = monorepo / SV154_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    assert safe, f"unsafe report content: {reason}"
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Activation: **{report.operational_activation_state}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 15.4 hardens privacy-safe analytics ingestion contracts. "
        "Production transmission remains disabled. "
        "No aggregations/dashboard. Slice 15.7 not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
