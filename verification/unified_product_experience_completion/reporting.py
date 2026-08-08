"""Report writer for Slice 14.14."""

from __future__ import annotations

import json
from pathlib import Path

from verification.unified_product_experience_completion.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1414_OUTPUT_RELATIVE,
)
from verification.unified_product_experience_completion.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.unified_product_experience_completion.models import (
    UnifiedProductExperienceCompletionReport,
)


def write_report(
    monorepo: Path, report: UnifiedProductExperienceCompletionReport
) -> Path:
    out_dir = monorepo / SV1414_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    assert safe, f"unsafe report content: {reason}"
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Epic complete: **{report.epic_complete}**\n\n"
        f"Completed slices: {report.completed_slices}/{report.total_slices}\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Epic 14 – Unified CodeStrata Community Experience is complete for the "
        "CodeStrata v0.2.0 epic scope when verdict is PASS or PASS_WITH_LIMITATIONS.\n\n"
        "Completion means product-experience scope is complete. It does not mean "
        "v0.2.0 is tagged or released. Tagging occurs only after the full E2E smoke "
        "gate. Epic 15 not started. No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
