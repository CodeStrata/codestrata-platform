"""Write verification report artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_vscode_clean_install.contract import (
    REPORT_JSON,
    REPORT_MD,
    SV1721_OUTPUT_RELATIVE,
)
from verification.community_vscode_clean_install.models import Report


def write_report(monorepo: Path, report: Report) -> Path:
    out_dir = monorepo / SV1721_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    assert "timestamp" not in text
    assert "/Users/" not in text
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {report.schema}:{report.schema_version}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        f"start_slice_17_21={report.epic17_boundary.get('start_slice_17_21')} "
        f"start_slice_17_22={report.epic17_boundary.get('start_slice_17_22')}\n\n"
        "Marketplace publish deferred. Slice 17.22 not started.\n",
        encoding="utf-8",
    )
    return json_path
