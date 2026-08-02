"""Read-only Finding correlation diagnostics.

Usage::

    python -m validation.finding_correlations
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codestrata.application.findings.correlation import correlate_findings
from codestrata.domain.findings.models import Finding
from validation.paths import RESULTS_DIR
from validation.recording import (
    list_run_ids,
    load_repository_validation_record,
    repository_records_root,
)
from validation.summary_from_records import list_repository_ids_with_records


def _findings_from_record(record: object) -> tuple[Finding, ...]:
    actual = getattr(record, "actual", None) or {}
    raw = actual.get("findings") if isinstance(actual, dict) else None
    if not isinstance(raw, list):
        return ()
    out: list[Finding] = []
    for item in raw:
        if isinstance(item, dict):
            try:
                out.append(Finding.model_validate(item))
            except Exception:  # noqa: BLE001
                continue
    return tuple(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m validation.finding_correlations",
        description="Internal Finding correlation diagnostics (read-only).",
    )
    parser.add_argument("--records-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--repository")
    parser.add_argument("--type")
    parser.add_argument("--cross-head", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repositories = list_repository_ids_with_records(records_root=args.records_dir)
    if args.repository:
        repositories = tuple(item for item in repositories if item == args.repository)

    rows: list[dict] = []
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
        findings = _findings_from_record(record)
        if not findings:
            continue
        result = correlate_findings(findings)
        for item in result.correlations:
            if args.type and item.correlation_type.value != args.type:
                continue
            if args.cross_head and len(set(item.assessment_head_ids)) < 2:
                continue
            rows.append(
                {
                    "repository": repository_id,
                    "correlation_id": item.correlation_id,
                    "correlation_type": item.correlation_type.value,
                    "finding_ids": list(item.finding_ids),
                    "primary_finding_id": item.primary_finding_id,
                    "assessment_head_ids": list(item.assessment_head_ids),
                    "confidence": item.confidence.level.value,
                    "basis": [b.value for b in item.basis],
                }
            )

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    elif not rows:
        print("No Finding correlations in selected records.")
    else:
        for row in rows:
            print(
                f"{row['repository']} | {row['correlation_id']} | "
                f"{row['correlation_type']} | {','.join(row['finding_ids'])}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
