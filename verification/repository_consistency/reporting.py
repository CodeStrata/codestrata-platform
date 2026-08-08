"""Report writer for Slice 16.8."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV168_OUTPUT_RELATIVE,
)
from verification.repository_consistency.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.repository_consistency.models import RepositoryConsistencyReport


def write_report(monorepo: Path, report: RepositoryConsistencyReport) -> Path:
    out_dir = monorepo / SV168_OUTPUT_RELATIVE
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
        "Slice 16.8 validates repository-wide consistency after Epic 16 cleanup. "
        "Validation-first. Slice 16.9 not started. "
        "No commit/tag/publish/deploy/remote/cutover.\n",
        encoding="utf-8",
    )
    return json_path
