"""Report writer for Slice 17.6."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_runtime_security.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV176_OUTPUT_RELATIVE,
)
from verification.community_cloud_runtime_security.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_runtime_security.models import CommunityCloudRuntimeSecurityReport


def write_report(monorepo: Path, report: CommunityCloudRuntimeSecurityReport) -> Path:
    out_dir = monorepo / SV176_OUTPUT_RELATIVE
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
        "Slice 17.6 — runtime security. Secrets identifiers + operational values in "
        "Secrets Manager only. Ingestion OFF. Writer unattached (deferred to 17.7). "
        "Slice 17.7 started; ingestion authority moved.\n",
        encoding="utf-8",
    )
    return json_path
