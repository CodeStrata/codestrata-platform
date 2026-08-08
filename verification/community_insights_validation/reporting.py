"""Report writer for Slice 15.11 validation verification."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1511_OUTPUT_RELATIVE,
)
from verification.community_insights_validation.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_insights_validation.models import CommunityInsightsValidationReport


def write_report(
    monorepo: Path, report: CommunityInsightsValidationReport
) -> Path:
    out_dir = monorepo / SV1511_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    assert safe, f"unsafe report content: {reason}"
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Policy: `{report.policy_id}:{report.policy_version}`\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 15.11 validates the offline Community Insights path end-to-end. "
        "No production deploy, ingestion, AWS calls, or Slice 15.12 start.\n",
        encoding="utf-8",
    )
    return json_path
