"""Report writers for Slice 14.11."""

from __future__ import annotations

import json
from pathlib import Path

from verification.responsive_accessibility.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1411_OUTPUT_RELATIVE,
)
from verification.responsive_accessibility.models import ResponsiveAccessibilityReport


def write_report(monorepo: Path, report: ResponsiveAccessibilityReport) -> Path:
    out_dir = monorepo / SV1411_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    assert "/Users/" not in text
    assert "/home/" not in text
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 14.11 validates the Epic 14 visual experience against a WCAG 2.2 "
        "AA-oriented accessibility and responsive contract. Automated verification "
        "is not a substitute for formal accessibility certification. Report content, "
        "scoring, risk semantics, report IA, brand geometry, schemas, and runtime "
        "behaviour are unchanged. Slice 14.13 complete. Slice 15.7 not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
