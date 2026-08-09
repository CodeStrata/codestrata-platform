"""Report writer for Slice 17.11."""

from __future__ import annotations

from pathlib import Path

from verification.community_production_site_ux_access.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1711_OUTPUT_RELATIVE,
)
from verification.community_production_site_ux_access.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_production_site_ux_access.models import Report


def write_report(monorepo: Path, report: Report) -> Path:
    out_dir = monorepo / SV1711_OUTPUT_RELATIVE
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
        "Slice 17.11 — production site UX and access validation for Community Docs and "
        "Insights. Verifies docs navigation/footer/favicon fixes, Insights favicon and "
        "shared-password auth RCA, and private-repo/public-site posture. "
        "Slice 17.12 not started.\n",
        encoding="utf-8",
    )
    return json_path
