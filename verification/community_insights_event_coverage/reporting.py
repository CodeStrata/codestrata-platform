"""Report writer for Slice 15.3."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_event_coverage.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV153_OUTPUT_RELATIVE,
)
from verification.community_insights_event_coverage.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_insights_event_coverage.models import (
    CommunityInsightsEventCoverageReport,
)


def write_report(
    monorepo: Path, report: CommunityInsightsEventCoverageReport
) -> Path:
    out_dir = monorepo / SV153_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    assert safe, f"unsafe report content: {reason}"
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Model adoption privacy decision: **{report.model_adoption_privacy_decision}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 15.3 validates that existing Community Cloud event contracts "
        "contain privacy-safe fields for planned Insights metrics. "
        "No schema activation. No aggregations/APIs/UI. "
        "Slice 15.7 not started. No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
