"""Report writer for Slice 17.1."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_cicd_architecture.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV171_OUTPUT_RELATIVE,
)
from verification.community_cloud_cicd_architecture.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_cicd_architecture.models import CommunityCloudCicdArchitectureReport


def write_report(monorepo: Path, report: CommunityCloudCicdArchitectureReport) -> Path:
    out_dir = monorepo / SV171_OUTPUT_RELATIVE
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
        "Slice 17.1 — CI/CD architecture frozen. "
        "Slice 17.2 not started. No AWS create/apply/deploy/commit/tag/publish.\n",
        encoding="utf-8",
    )
    return json_path
