"""Write Community Data Lake completion verification report (Slice 8.15)."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_completion.models import CompletionReport

REPORT_FILENAME = "community-data-lake-completion-verification.json"


def write_completion_report(report: CompletionReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / REPORT_FILENAME
    report.write(path)
    return path


__all__ = ["REPORT_FILENAME", "write_completion_report"]
