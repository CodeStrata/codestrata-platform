"""Read-only CLI for internal false-positive tracking.

Usage::

    python -m validation.false_positives list
    python -m validation.false_positives show <fp-id>
    python -m validation.false_positives summarize
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codestrata.domain.quality_metrics.false_positives import FalsePositiveRecord
from validation.false_positives.adjudication import ADJUDICATIONS_DIR
from validation.paths import RESULTS_DIR
from validation.recording import (
    list_run_ids,
    load_repository_validation_record,
    repository_records_root,
)
from validation.summary_from_records import (
    aggregate_false_positive_tracking,
    list_repository_ids_with_records,
)


def _load_all_records(*, records_root: Path) -> tuple:
    from validation.recording import RepositoryValidationRecord

    records: list[RepositoryValidationRecord] = []
    for repository_id in list_repository_ids_with_records(records_root=records_root):
        run_ids = list_run_ids(repository_id, records_root=records_root)
        if not run_ids:
            continue
        record_dir = (
            repository_records_root(repository_id, records_root=records_root)
            / "runs"
            / run_ids[-1]
        )
        try:
            records.append(load_repository_validation_record(record_dir))
        except Exception as exc:  # noqa: BLE001
            print(f"skip {repository_id}: {exc}", file=sys.stderr)
    return tuple(records)


def _filter_fps(
    records: tuple,
    *,
    repository: str | None,
    area: str | None,
    rule: str | None,
    status: str | None,
    classification: str | None,
    open_only: bool,
) -> list[dict]:
    tracking = aggregate_false_positive_tracking(records)
    items = list(tracking.records)
    if repository:
        items = [item for item in items if item.get("repository_id") == repository]
    if area:
        items = [item for item in items if str(item.get("assessment_area", "")).startswith(area)]
    if rule:
        items = [item for item in items if item.get("rule_id") == rule]
    if status:
        items = [item for item in items if item.get("status") == status]
    if classification:
        items = [item for item in items if item.get("classification") == classification]
    if open_only:
        items = [
            item
            for item in items
            if item.get("status") in {"open", "investigating"}
        ]
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m validation.false_positives",
        description="Internal false-positive tracking (read-only).",
    )
    parser.add_argument(
        "--records-dir",
        type=Path,
        default=RESULTS_DIR,
        help="Validation records root (default: validation/results)",
    )
    parser.add_argument(
        "--adjudications-dir",
        type=Path,
        default=ADJUDICATIONS_DIR,
        help="Committed adjudications directory",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List tracked false positives")
    list_p.add_argument("--repository")
    list_p.add_argument("--area")
    list_p.add_argument("--rule")
    list_p.add_argument("--status")
    list_p.add_argument("--classification")
    list_p.add_argument("--open-only", action="store_true")

    show_p = sub.add_parser("show", help="Show one false positive by id")
    show_p.add_argument("fp_id")

    sub.add_parser("summarize", help="Summarize false-positive tracking counts")

    args = parser.parse_args(argv)
    records = _load_all_records(records_root=args.records_dir)

    if args.command == "list":
        items = _filter_fps(
            records,
            repository=args.repository,
            area=args.area,
            rule=args.rule,
            status=args.status,
            classification=args.classification,
            open_only=args.open_only,
        )
        if args.json:
            print(json.dumps(items, indent=2, sort_keys=True))
        else:
            for item in items:
                print(
                    f"{item.get('false_positive_id')} | {item.get('repository_id')} | "
                    f"{item.get('assessment_area')} | {item.get('classification')} | "
                    f"{item.get('status')}"
                )
        return 0

    if args.command == "show":
        items = _filter_fps(
            records,
            repository=None,
            area=None,
            rule=None,
            status=None,
            classification=None,
            open_only=False,
        )
        match = next((item for item in items if item.get("false_positive_id") == args.fp_id), None)
        if match is None:
            # Validate id shape even when missing.
            if not str(args.fp_id).startswith("fp:"):
                print("false_positive_id must start with fp:", file=sys.stderr)
                return 2
            print(f"not found: {args.fp_id}", file=sys.stderr)
            return 1
        FalsePositiveRecord.model_validate(match)  # schema check
        print(json.dumps(match, indent=2, sort_keys=True))
        return 0

    if args.command == "summarize":
        tracking = aggregate_false_positive_tracking(records)
        payload = tracking.model_dump(mode="json")
        payload.pop("records", None)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(
                f"total={tracking.total} suspected={tracking.suspected} "
                f"confirmed={tracking.confirmed} ambiguous={tracking.ambiguous} "
                f"expectation_errors={tracking.expectation_errors} "
                f"fixed={tracking.fixed} open={tracking.open}"
            )
            if tracking.by_pack:
                print("by_pack:", json.dumps(tracking.by_pack, sort_keys=True))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
