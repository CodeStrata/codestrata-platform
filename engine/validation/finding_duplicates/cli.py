"""Read-only Finding duplicate diagnostics.

Usage::

    python -m validation.finding_duplicates
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codestrata.application.findings.consolidation import consolidate_findings
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
        comparison = getattr(record, "comparison", None) or {}
        raw = comparison.get("findings") if isinstance(comparison, dict) else None
    if not isinstance(raw, list):
        return ()
    out: list[Finding] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(Finding.model_validate(item))
        except Exception:  # noqa: BLE001
            continue
    return tuple(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m validation.finding_duplicates",
        description="Internal Finding duplicate consolidation diagnostics (read-only).",
    )
    parser.add_argument(
        "--records-dir",
        type=Path,
        default=RESULTS_DIR,
        help="Validation records root",
    )
    parser.add_argument("--repository")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repositories = list_repository_ids_with_records(records_root=args.records_dir)
    if args.repository:
        repositories = tuple(
            item for item in repositories if item == args.repository
        )

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
        result = consolidate_findings(findings)
        for group in result.duplicate_groups:
            rows.append(
                {
                    "repository": repository_id,
                    "canonical_finding_id": group.canonical_finding_id,
                    "member_finding_ids": list(group.member_finding_ids),
                    "duplicate_kind": group.duplicate_kind.value,
                    "consolidation_basis": [item.value for item in group.consolidation_basis],
                    "limitations": list(group.limitations),
                }
            )
        if result.diagnostics.unresolved_duplicate_candidate_count:
            rows.append(
                {
                    "repository": repository_id,
                    "unresolved_candidates": (
                        result.diagnostics.unresolved_duplicate_candidate_count
                    ),
                }
            )

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        if not rows:
            print("No duplicate Finding groups in selected records.")
            return 0
        for row in rows:
            if "canonical_finding_id" not in row:
                print(
                    f"{row.get('repository')} | unresolved="
                    f"{row.get('unresolved_candidates')}"
                )
                continue
            print(
                f"{row['repository']} | {row['canonical_finding_id']} | "
                f"{row['duplicate_kind']} | members="
                f"{','.join(row['member_finding_ids'])}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
