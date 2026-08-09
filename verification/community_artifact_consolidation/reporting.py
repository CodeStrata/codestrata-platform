"""Report writer for Slice 17.12."""

from __future__ import annotations

from pathlib import Path

from verification.community_artifact_consolidation.determinism import dict_to_canonical_json
from verification.community_artifact_consolidation.models import Report


def write_report(monorepo: Path, report: Report, relative_dir: str, json_name: str, md_name: str) -> Path:
    out_dir = monorepo / relative_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    text = dict_to_canonical_json(payload)
    json_path = out_dir / json_name
    json_path.write_text(text, encoding="utf-8")
    md = (
        f"# {report.schema}:{report.schema_version}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 17.12 — consolidate runtime artifacts under `.codestrata-artifacts/`.\n"
        "Slice 17.13 not started. No commit/tag/publish.\n"
    )
    (out_dir / md_name).write_text(md, encoding="utf-8")
    return json_path
