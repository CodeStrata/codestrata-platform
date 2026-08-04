"""Reporting helpers for SV.13."""

from __future__ import annotations

from pathlib import Path

from verification.system_defect_fixes.contract import (
    DATASET_DISCLAIMER,
    LEDGER_JSON,
    VERIFICATION_JSON,
    VERIFICATION_MD,
)
from verification.system_defect_fixes.models import Sv13VerificationReport


def write_verification_outputs(
    report: Sv13VerificationReport,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report.write_json(output_dir / VERIFICATION_JSON)
    if report.ledger is not None:
        import json

        (output_dir / LEDGER_JSON).write_text(
            json.dumps(report.ledger.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    lines = [
        "# SV.13 System Defect Fix Verification",
        "",
        f"Verdict: **{report.verdict}**",
        "",
        f"Repository population: {report.repository_count}",
        "",
        DATASET_DISCLAIMER,
        "",
        "## Checks",
        "",
    ]
    for check in report.checks:
        mark = "PASS" if check.ok else "FAIL"
        lines.append(f"- [{mark}] `{check.name}` — {check.detail}")
    lines.extend(["", "## Identities", ""])
    lines.append(f"- dataset_id: `{report.dataset_id}`")
    lines.append(f"- aggregation_id: `{report.aggregation_id}`")
    lines.append(f"- eir_report_id: `{report.eir_report_id}`")
    lines.append(
        f"- interpretation_policy_bundle_id: `{report.interpretation_policy_bundle_id}`"
    )
    lines.append(f"- website_export_id: `{report.website_export_id}`")
    lines.append("")
    (output_dir / VERIFICATION_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
