"""Reporting helpers for Slice 13.15."""

from __future__ import annotations

from pathlib import Path

from verification.vscode_epic13_completion.models import VsCodeEpic13CompletionReport
from verification.vscode_epic13_completion.runner import write_report


def persist(monorepo: Path, report: VsCodeEpic13CompletionReport) -> Path:
    return write_report(monorepo, report)
