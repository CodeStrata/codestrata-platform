"""Report writer for Slice 15.8."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_application.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV158_OUTPUT_RELATIVE,
)
from verification.community_insights_application.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_insights_application.models import (
    CommunityInsightsApplicationReport,
)


def write_report(
    monorepo: Path, report: CommunityInsightsApplicationReport
) -> Path:
    out_dir = monorepo / SV158_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    assert safe, f"unsafe report content: {reason}"
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Future repository: `{report.future_repository}`\n\n"
        f"Future host: `{report.future_host}`\n\n"
        f"Stack: `{report.stack}`\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 15.8 builds the Insights application shell and export boundary. "
        "Authentication owned by Slice 15.9. No production deploy. Slice 15.10 not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
