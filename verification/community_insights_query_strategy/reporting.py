"""Report writer for Slice 15.5."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_query_strategy.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV155_OUTPUT_RELATIVE,
)
from verification.community_insights_query_strategy.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_insights_query_strategy.models import (
    CommunityInsightsQueryStrategyReport,
)


def write_report(
    monorepo: Path, report: CommunityInsightsQueryStrategyReport
) -> Path:
    out_dir = monorepo / SV155_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    assert safe, f"unsafe report content: {reason}"
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Direct S3 preferred: **{report.direct_s3_preferred}**\n\n"
        f"Athena required: **{report.athena_required}**\n\n"
        f"Lifetime strategy: `{report.lifetime_strategy}`\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 15.5 validates bounded S3 query/read strategy for future "
        "on-demand Insights aggregation. No aggregation/dashboard runtime. "
        "Slice 15.7 not started. No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
