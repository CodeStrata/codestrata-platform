"""Report writer for Slice 16.1."""

from __future__ import annotations

from pathlib import Path

from verification.repository_inventory.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV161_OUTPUT_RELATIVE,
)
from verification.repository_inventory.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.repository_inventory.models import RepositoryInventoryReport


def write_report(monorepo: Path, report: RepositoryInventoryReport) -> Path:
    out_dir = monorepo / SV161_OUTPUT_RELATIVE
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
        f"Inventory entries: {report.inventory_summary.get('entry_count', 0)}\n\n"
        "Slice 16.1 is audit-only. No files were deleted, renamed, or moved. "
        "Cleanup actions are deferred to Slice 16.2. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
