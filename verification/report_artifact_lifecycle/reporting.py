"""Report writer for Slice 17.15."""

from __future__ import annotations

from pathlib import Path

from verification.report_artifact_lifecycle.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1715_OUTPUT_RELATIVE,
)
from verification.report_artifact_lifecycle.determinism import dict_to_canonical_json, report_text_is_safe
from verification.report_artifact_lifecycle.models import Report


def write_report(monorepo: Path, report: Report) -> Path:
    out_dir = monorepo / SV1715_OUTPUT_RELATIVE
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
        "Slice 17.15 — human-readable repository/portfolio folder identity with "
        "current/previous slot retention (max 2 versions). Run IDs are manifest "
        "metadata only. Data Lake and validation artifacts excluded from report retention.\n",
        encoding="utf-8",
    )
    return json_path
