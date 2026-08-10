"""Write Slice 17.19 verification report artifacts."""

from __future__ import annotations

from pathlib import Path

from verification.community_assessment_engineering_intelligence.contract import (
    REPORT_JSON,
    REPORT_MD,
)
from verification.community_assessment_engineering_intelligence.determinism import (
    dict_to_canonical_json,
)
from verification.community_assessment_engineering_intelligence.models import Report


def write_report(output_dir: Path, report: Report) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    json_path = output_dir / REPORT_JSON
    json_path.write_text(dict_to_canonical_json(payload), encoding="utf-8")
    md_path = output_dir / REPORT_MD
    lines = [
        f"# {report.package_id}",
        "",
        f"- verdict: `{report.verdict}`",
        f"- slice: `{report.slice}`",
        f"- checks: {report.total_checks}",
        f"- failed: {report.failed_checks}",
        f"- start_slice_17_19: `{report.epic17_boundary.get('start_slice_17_19')}`",
        f"- start_slice_17_20: `{report.epic17_boundary.get('start_slice_17_20')}`",
        f"- start_slice_17_21: `{report.epic17_boundary.get('start_slice_17_21')}`",
        f"- eir_generated: `{report.eir_generation.get('generated')}`",
        f"- repository_count: `{report.eir_generation.get('repository_count')}`",
        "",
        "## Limitations",
        "",
    ]
    for item in report.limitations:
        lines.append(f"- `{item}`")
    if not report.limitations:
        lines.append("- none")
    lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path
