"""Determinism helper for Slice 12.6."""

from __future__ import annotations

import hashlib
from pathlib import Path

from verification.infrastructure_repository_exporter.runner import build_report, write_verification_outputs


def report_digest(monorepo: Path) -> bytes:
    report = build_report(monorepo)
    path = write_verification_outputs(report, monorepo)
    return path.read_bytes()


def digests_match(monorepo: Path) -> tuple[bool, str, str]:
    a = report_digest(monorepo)
    b = report_digest(monorepo)
    ha = hashlib.sha256(a).hexdigest()
    hb = hashlib.sha256(b).hexdigest()
    return a == b, ha, hb
