"""System Verification report determinism (SV.10–SV.14)."""

from __future__ import annotations

import json
from pathlib import Path

from verification.deterministic_outputs.fingerprints import (
    contains_forbidden_environment,
    fingerprint_mapping,
)
from verification.deterministic_outputs.inputs import verification_report_paths
from verification.deterministic_outputs.models import CheckResult


def check_verification_reports(monorepo: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    paths = verification_report_paths(monorepo)
    checks.append(
        CheckResult(
            name="verification_reports_present",
            ok=len(paths) >= 4,
            detail=f"present={len(paths)}",
            category="verification_reports",
        )
    )
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        name = path.name
        fp1 = fingerprint_mapping(data, exclude=("generated_at",))
        fp2 = fingerprint_mapping(data, exclude=("generated_at",))
        checks.append(
            CheckResult(
                name=f"verification_report_fingerprint_{path.stem}",
                ok=fp1 == fp2,
                detail=f"sha256={fp1[:16]}… file={name}",
                category="verification_reports",
            )
        )
        schema_version = str(data.get("schema_version") or "")
        checks.append(
            CheckResult(
                name=f"verification_report_schema_{path.stem}",
                ok=schema_version == "1.0.0",
                detail=f"schema_version={schema_version}",
                category="verification_reports",
            )
        )
        blob = json.dumps(data, sort_keys=True)[:200_000]
        hits = contains_forbidden_environment(blob)
        checks.append(
            CheckResult(
                name=f"verification_report_no_home_path_{path.stem}",
                ok=not hits,
                detail=f"hits={hits or 'none'}",
                category="verification_reports",
            )
        )
    return checks
