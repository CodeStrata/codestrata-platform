"""Reporting helpers for Slice 17.22."""

from __future__ import annotations

from pathlib import Path

from verification.community_epic17_defect_resolution.models import Report
from verification.community_epic17_defect_resolution.runner import write_report


def emit_report(monorepo: Path, report: Report) -> Path:
    return write_report(monorepo, report)
