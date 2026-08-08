"""Report writer for Slice 15.12."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1512_OUTPUT_RELATIVE,
)
from verification.community_insights_completion.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_insights_completion.models import (
    CommunityInsightsCompletionReport,
)


def write_report(
    monorepo: Path, report: CommunityInsightsCompletionReport
) -> Path:
    out_dir = monorepo / SV1512_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    assert safe, f"unsafe report content: {reason}"
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Epic complete: **{report.epic_complete}**\n\n"
        f"Completed slices: {report.completed_slices}/{report.total_slices}\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Epic 15 – Community Insights is complete for the CodeStrata epic scope "
        "when verdict is PASS or PASS_WITH_LIMITATIONS.\n\n"
        "Completion means insights architecture and dashboard scope are complete. "
        "It does not enable production ingestion, deploy insights.codestrata.ai, "
        "create real secrets, or start Epic 16.\n",
        encoding="utf-8",
    )
    return json_path
