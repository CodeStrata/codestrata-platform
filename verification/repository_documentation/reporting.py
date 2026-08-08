"""Report writer for Slice 16.2."""

from __future__ import annotations

from pathlib import Path

from verification.repository_documentation.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV162_OUTPUT_RELATIVE,
)
from verification.repository_documentation.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.repository_documentation.models import RepositoryDocumentationReport


def write_report(monorepo: Path, report: RepositoryDocumentationReport) -> Path:
    out_dir = monorepo / SV162_OUTPUT_RELATIVE
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
        "Slice 16.2 is documentation-only cleanup for Community public readiness. "
        "Historical knowledge was not deleted. Slice 16.3 was not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
