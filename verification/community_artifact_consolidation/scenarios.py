"""Scenarios for Slice 17.12."""

from __future__ import annotations

from verification.community_artifact_consolidation.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    scenarios = [
        ("A", "artifact root missing from engine", flags.get("engine_package", False)),
        ("B", "assessment still defaults to reports/", flags.get("default_output", False)),
        ("C", "heads not under heads/", flags.get("heads_writer", False)),
        ("D", "assessment.json is giant merge", flags.get("lightweight_manifest", False)),
        ("E", "verification still writes reports/verification", flags.get("validation_paths", False)),
        ("F", "Data Lake auto-upload enabled", flags.get("data_lake_forbidden", False)),
        ("G", "VS Code still defaults to reports", flags.get("vscode_default", False)),
        ("H", ".codestrata-artifacts not gitignored", flags.get("gitignore", False)),
        ("I", "Slice 17.13 started", flags.get("slice_17_13_absent", False)),
        ("J", "duplicate runtime report roots required", flags.get("single_root", False)),
    ]
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), label if ok else f"FAIL:{label}", "scenarios"))
        if not ok:
            defects.append(Defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
