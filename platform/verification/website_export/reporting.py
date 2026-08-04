"""Write SV.8 verification report."""

from __future__ import annotations

from pathlib import Path

from verification.website_export.models import VerificationReport


def write_verification_report(report: VerificationReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "website-export-verification.json"
    report.write(path)
    return path
