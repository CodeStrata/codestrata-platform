"""Write Community Data Lake verification report (Slice 8.14)."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake.models import VerificationReport


def write_verification_report(report: VerificationReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "community-data-lake-verification.json"
    report.write(path)
    return path


__all__ = ["write_verification_report"]
