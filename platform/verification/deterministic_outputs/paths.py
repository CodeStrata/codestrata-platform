"""Path-independence helpers."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from verification.deterministic_outputs.fingerprints import contains_forbidden_environment
from verification.deterministic_outputs.models import CheckResult


def check_paths_in_sample_reports(reports: list[dict]) -> list[CheckResult]:
    hits_total: list[str] = []
    for report in reports:
        blob = json.dumps(report, sort_keys=True)[:500_000]
        hits_total.extend(contains_forbidden_environment(blob))
    unique = sorted(set(hits_total))
    return [
        CheckResult(
            name="paths_no_home_or_users_in_canonical_reports",
            ok=not unique,
            detail=f"hits={unique or 'none'}",
            category="paths",
        )
    ]


def check_temp_dir_independence_fingerprint(build_fn) -> CheckResult:
    """Run a builder that returns fingerprintable bytes in two temp dirs."""

    with tempfile.TemporaryDirectory(prefix="sv15a_") as a:
        with tempfile.TemporaryDirectory(prefix="sv15 b with spaces_") as b:
            left = build_fn(Path(a))
            right = build_fn(Path(b))
    return CheckResult(
        name="paths_temp_dir_independence",
        ok=left == right,
        detail="two temp dirs (incl. spaces) → identical builder output",
        category="paths",
    )
