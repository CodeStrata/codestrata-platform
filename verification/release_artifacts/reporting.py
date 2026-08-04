"""Reporting helpers for SV.16 release artifact verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.release_artifacts.contract import (
    DATASET_DISCLAIMER,
    INTENDED_RELEASE_VERSION,
    RELEASE_NOTES_INPUT_JSON,
    REPORT_JSON,
    REPORT_MD,
)
from verification.release_artifacts.models import Sv16VerificationReport


def write_verification_outputs(
    report: Sv16VerificationReport,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report.write_json(output_dir / REPORT_JSON)

    lines = [
        "# SV.16 Release Artifact Verification",
        "",
        f"Verdict: **{report.verdict}**",
        "",
        f"Intended release: {report.intended_release_version}",
        f"Repositories: {report.repository_count}",
        f"Checks: {sum(1 for c in report.checks if c.ok)}/{len(report.checks)}",
        f"Defects: {len(report.defects)}",
        f"Blockers: {len(report.blockers)}",
        f"Warnings: {len(report.warnings)}",
        "",
        DATASET_DISCLAIMER,
        "",
        "## Confirmations",
        "",
    ]
    for key, value in sorted(report.confirmations.items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Checks", ""])
    for check in report.checks:
        mark = "PASS" if check.ok else "FAIL"
        lines.append(f"- [{mark}] `{check.name}` — {check.detail}")
    if report.blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in report.blockers:
            lines.append(f"- `{blocker.code}` — {blocker.detail}")
    if report.defects:
        lines.extend(["", "## Defects", ""])
        for defect in report.defects:
            lines.append(
                f"- `{defect.classification}` {defect.component}: "
                f"expected={defect.expected} actual={defect.actual}"
            )
    if report.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in report.warnings:
            lines.append(f"- `{warning.code}` — {warning.detail}")
    if report.limitations:
        lines.extend(["", "## Limitations", ""])
        for item in report.limitations:
            lines.append(f"- {item}")
    (output_dir / REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")

    release_notes = {
        "intended_release_version": INTENDED_RELEASE_VERSION,
        "verdict": report.verdict,
        "verification_id": report.verification_id,
        "repository_count": report.repository_count,
        "ei_identities": dict(report.ei_identities),
        "artifact_paths": dict(report.artifact_paths),
        "checksums": dict(report.checksums),
        "limitations": list(report.limitations),
        "defect_count": len(report.defects),
        "warning_count": len(report.warnings),
        "blocker_count": len(report.blockers),
        "opentofu": {
            "tool_available": any(
                c.name == "opentofu:tool_available" and c.ok for c in report.checks
            ),
            "version_detail": next(
                (
                    c.detail
                    for c in report.checks
                    if c.name == "opentofu:tool_available"
                ),
                "",
            ),
            "fmt_passed": any(
                c.name == "opentofu:fmt_check" and c.ok for c in report.checks
            ),
            "validate_module_passed": any(
                c.name == "opentofu:validate:module" and c.ok for c in report.checks
            ),
            "validate_production_passed": any(
                c.name == "opentofu:validate:production" and c.ok for c in report.checks
            ),
            "terraform_0_11_not_used": any(
                c.name.startswith("opentofu:terraform_0_11") and c.ok
                for c in report.checks
            ),
            "no_plan_or_apply": any(
                c.name == "opentofu:no_plan_or_apply" and c.ok for c in report.checks
            ),
            "blocker_closed": any(
                c.name == "opentofu:blocker_closed" and c.ok for c in report.checks
            ),
        },
    }
    (output_dir / RELEASE_NOTES_INPUT_JSON).write_text(
        json.dumps(release_notes, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
