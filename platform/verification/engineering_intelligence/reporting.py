"""Write SV.6 verification report artifacts (privacy-safe)."""

from __future__ import annotations

from pathlib import Path

from verification.engineering_intelligence.models import VerificationReport


def write_verification_report(report: VerificationReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "engineering-intelligence-verification.json"
    report.write(path)
    return path
