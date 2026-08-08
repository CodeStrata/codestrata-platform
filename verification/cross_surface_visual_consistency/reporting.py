"""Report writer for Slice 14.13."""

from __future__ import annotations

import json
from pathlib import Path

from verification.cross_surface_visual_consistency.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1413_OUTPUT_RELATIVE,
)
from verification.cross_surface_visual_consistency.models import CrossSurfaceVisualConsistencyReport


def write_report(monorepo: Path, report: CrossSurfaceVisualConsistencyReport) -> Path:
    out_dir = monorepo / SV1413_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    assert "/Users/" not in text
    assert "/home/" not in text
    assert "timestamp" not in text.lower()
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 14.13 validates cross-surface visual consistency across Docs, "
        "Assessment HTML, EIR HTML, VS Code, Marketplace, and API portal surfaces. "
        "Design System remains 1.0. Slice 15.7 not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
