"""Read-only Finding severity calibration diagnostics.

Usage::

    python -m validation.severity_calibration --changed-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codestrata.application.findings.severity_calibration import calibrate_finding_severity
from validation.paths import RESULTS_DIR
from validation.recording import (
    list_run_ids,
    load_repository_validation_record,
    repository_records_root,
)
from validation.summary_from_records import list_repository_ids_with_records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m validation.severity_calibration",
        description="Internal Finding severity calibration diagnostics (read-only).",
    )
    parser.add_argument("--records-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--repository")
    parser.add_argument("--rule")
    parser.add_argument("--head")
    parser.add_argument("--changed-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repositories = list_repository_ids_with_records(records_root=args.records_dir)
    if args.repository:
        repositories = tuple(item for item in repositories if item == args.repository)

    rows: list[dict] = []
    summary = {
        "findings_evaluated": 0,
        "unchanged_count": 0,
        "increased_count": 0,
        "decreased_count": 0,
        "provisional_count": 0,
        "legacy_count": 0,
    }
    rank = {
        "informational": 0,
        "info": 0,
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }

    for repository_id in repositories:
        run_ids = list_run_ids(repository_id, records_root=args.records_dir)
        if not run_ids:
            continue
        record_dir = (
            repository_records_root(repository_id, records_root=args.records_dir)
            / "runs"
            / run_ids[-1]
        )
        try:
            record = load_repository_validation_record(record_dir)
        except Exception as exc:  # noqa: BLE001
            print(f"skip {repository_id}: {exc}", file=sys.stderr)
            continue
        actual = getattr(record, "actual", None) or {}
        findings = actual.get("findings") if isinstance(actual, dict) else None
        if not isinstance(findings, list):
            continue
        for item in findings:
            if not isinstance(item, dict):
                continue
            rule_id = str(item.get("rule_id") or "")
            if not rule_id:
                continue
            if args.rule and rule_id != args.rule:
                continue
            if args.head and not rule_id.startswith(f"{args.head}."):
                continue
            emitted = str(item.get("severity") or "informational")
            assessment = calibrate_finding_severity(
                rule_id=rule_id,
                emitted_severity=emitted,
                metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
                evidence_paths=tuple(
                    str(row.get("path") or "")
                    for row in (item.get("evidence") or [])
                    if isinstance(row, dict) and row.get("path")
                ),
            )
            summary["findings_evaluated"] += 1
            if assessment.calibration_status.value == "provisional":
                summary["provisional_count"] += 1
            if assessment.calibration_status.value == "legacy":
                summary["legacy_count"] += 1
            before = rank.get(emitted.lower(), 0)
            after = rank.get(assessment.severity.value, 0)
            changed = before != after
            if not changed:
                summary["unchanged_count"] += 1
            elif after > before:
                summary["increased_count"] += 1
            else:
                summary["decreased_count"] += 1
            if args.changed_only and not changed:
                continue
            rows.append(
                {
                    "repository": repository_id,
                    "rule_id": rule_id,
                    "base_severity": (
                        assessment.component_summary.base_severity.value
                        if assessment.component_summary.base_severity
                        else None
                    ),
                    "emitted_severity": emitted,
                    "calibrated_severity": assessment.severity.value,
                    "calibration_status": assessment.calibration_status.value,
                    "policy_id": assessment.policy_id,
                    "context": assessment.component_summary.production_context,
                }
            )

    if args.json:
        print(json.dumps({"summary": summary, "rows": rows}, indent=2, sort_keys=True))
    else:
        print(
            "evaluated={findings_evaluated} unchanged={unchanged_count} "
            "increased={increased_count} decreased={decreased_count} "
            "provisional={provisional_count} legacy={legacy_count}".format(**summary)
        )
        for row in rows:
            print(
                f"{row['repository']} | {row['rule_id']} | "
                f"{row['emitted_severity']} -> {row['calibrated_severity']} | "
                f"{row['calibration_status']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
