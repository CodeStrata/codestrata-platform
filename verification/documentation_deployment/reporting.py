"""Report writers for Slice 14.12."""

from __future__ import annotations

import json
from pathlib import Path

from verification.documentation_deployment.contract import REPORT_JSON, REPORT_MD, SV1412_OUTPUT_RELATIVE
from verification.documentation_deployment.models import DocumentationDeploymentReport


def write_report(monorepo: Path, report: DocumentationDeploymentReport) -> Path:
    out_dir = monorepo / SV1412_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    assert "/Users/" not in text
    assert "/home/" not in text
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        "# documentation-deployment-verification:1.0.0\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 14.12 validates Cloudflare Static Assets deployment configuration "
        "for the docs package (model B). Build-once Approach A, local Wrangler, "
        "and output alignment are enforced. No production deploy. Slice 14.13 complete. "
        "Epic 15 not started. No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path
