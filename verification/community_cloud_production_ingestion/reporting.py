"""Report writer for Slice 17.7."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_production_ingestion.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV177_OUTPUT_RELATIVE,
)
from verification.community_cloud_production_ingestion.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_production_ingestion.models import (
    CommunityCloudProductionIngestionReport,
)


def write_report(monorepo: Path, report: CommunityCloudProductionIngestionReport) -> Path:
    out_dir = monorepo / SV177_OUTPUT_RELATIVE
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
        "Slice 17.7 — production ingestion. Writer attach + ingestion enablement "
        "with five-stream fixtures, privacy, quarantine, and failure isolation. "
        "Slice 17.8 not started.\n",
        encoding="utf-8",
    )
    return json_path
