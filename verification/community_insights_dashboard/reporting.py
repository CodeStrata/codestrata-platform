"""Report writer for Slice 15.10 dashboard verification."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_dashboard.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1510_OUTPUT_RELATIVE,
)
from verification.community_insights_dashboard.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_insights_dashboard.models import CommunityInsightsDashboardReport


def write_report(
    monorepo: Path, report: CommunityInsightsDashboardReport
) -> Path:
    out_dir = monorepo / SV1510_OUTPUT_RELATIVE
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
        "Slice 15.10 builds the presentation-only Community Insights dashboard with "
        "local CSS/SVG charts. No production deploy or ingestion. Slice 15.11 not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
