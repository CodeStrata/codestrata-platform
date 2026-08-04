"""Write SV.9 verification report."""

from __future__ import annotations

from pathlib import Path

from infrastructure.verification.models import VerificationReport


def write_verification_report(report: VerificationReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "platform-deployment-foundation-verification.json"
    report.write(path)
    return path
