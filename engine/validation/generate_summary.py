#!/usr/bin/env python3
"""Generate cross-repository validation summary artifacts (Epic 4 Slice 4.12).

Internal engineering tool. Does not execute assessments. Reads Slice 4.11
``record.json`` files only.

Examples::

    python -m validation.generate_summary
    python -m validation.generate_summary --local-only --print-summary
    python -m validation.generate_summary --repository local-sample-js --json-only
    python -m validation.run_validation --summarize --local-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from validation.matrix import ACTIVE_VALIDATION_SET
from validation.models import RepositorySourceType
from validation.paths import RESULTS_DIR
from validation.registry import RegistryError, load_all_repositories
from validation.summary_from_records import (
    RecordValidationError,
    generate_summary_from_records,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validation.generate_summary",
        description=(
            "Build validation-summary.json/.md from Slice 4.11 records "
            "(no assessment execution)."
        ),
    )
    parser.add_argument(
        "--records-dir",
        type=Path,
        default=None,
        help="Records root (default: engine/validation/results/).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Alias for --records-dir (summaries written under records/summaries/).",
    )
    parser.add_argument(
        "--repository",
        action="append",
        dest="repositories",
        default=[],
        help="Repository id to include (repeatable).",
    )
    parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        default=[],
        help="Only repositories with this registry tag (repeatable).",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Include only local fixture repositories from the registry.",
    )
    parser.add_argument(
        "--include-remote",
        action="store_true",
        help="When filtering, include remote repository records.",
    )
    parser.add_argument(
        "--run-id",
        action="append",
        default=[],
        metavar="REPO=RUN_ID",
        help="Explicit run id for a repository (repeatable).",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Write validation-summary.json only.",
    )
    parser.add_argument(
        "--markdown-only",
        action="store_true",
        help="Write validation-summary.md only.",
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print a short human summary to stdout.",
    )
    parser.add_argument(
        "--active-set",
        action="store_true",
        help="Limit to the active six-repository validation set.",
    )
    return parser


def _parse_run_ids(values: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise RecordValidationError(
                f"invalid --run-id {item!r}; expected REPO=RUN_ID"
            )
        repo, run_id = item.split("=", 1)
        repo = repo.strip()
        run_id = run_id.strip()
        if not repo or not run_id:
            raise RecordValidationError(f"invalid --run-id {item!r}")
        mapping[repo] = run_id
    return mapping


def select_repository_ids(args: argparse.Namespace) -> set[str] | None:
    """Resolve repository filter. ``None`` means all repositories that have records."""

    filtering = bool(
        args.repositories
        or args.tags
        or args.local_only
        or args.active_set
        or args.include_remote
    )
    if not filtering:
        return None

    try:
        definitions = load_all_repositories()
    except RegistryError as exc:
        raise RecordValidationError(str(exc)) from exc

    by_id = {item.repository_id: item for item in definitions}

    if args.active_set:
        selected = set(ACTIVE_VALIDATION_SET)
    elif args.repositories:
        selected = set(args.repositories)
    else:
        selected = set(by_id)

    if args.repositories:
        selected &= set(args.repositories)
        # Allow explicit ids even if not in registry (records may still exist).
        selected |= set(args.repositories)

    if args.tags:
        required = set(args.tags)
        selected = {
            rid
            for rid in selected
            if rid in by_id and required.issubset(set(by_id[rid].tags))
        }

    if args.local_only:
        selected = {
            rid
            for rid in selected
            if rid in by_id and by_id[rid].source_type == RepositorySourceType.LOCAL
        }
    elif args.include_remote:
        # Keep remotes that are already in selected.
        pass
    elif not args.repositories and not args.active_set:
        # Tag-only filter without local/remote flags: keep both source types.
        pass
    elif args.active_set and not args.include_remote and not args.local_only:
        # Active set includes the remote petclinic record when present.
        pass

    return selected


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.json_only and args.markdown_only:
        print(
            "error: --json-only and --markdown-only are mutually exclusive",
            file=sys.stderr,
        )
        return 2

    records_root = args.records_dir or args.output_dir or RESULTS_DIR
    write_json = not args.markdown_only
    write_markdown = not args.json_only

    try:
        run_ids = _parse_run_ids(args.run_id)
        repository_ids = select_repository_ids(args)
        # Explicit --repository lists must all be present; tag/local filters
        # summarize the intersection with available records.
        require_all = bool(args.repositories) or bool(run_ids)
        artifact, out_dir = generate_summary_from_records(
            records_root=records_root,
            repository_ids=repository_ids,
            run_ids=run_ids or None,
            write_json=write_json,
            write_markdown=write_markdown,
            require_all_requested=require_all,
        )
    except RecordValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Successful generation exits 0 regardless of overall_verdict (report-only).
    if args.print_summary:
        print(
            f"overall={artifact.overall_verdict.value} "
            f"repos={artifact.repository_count} "
            f"pass={artifact.verdict_totals.passed} "
            f"fail={artifact.verdict_totals.failed} "
            f"error={artifact.verdict_totals.errors} "
            f"skipped={artifact.verdict_totals.skipped}"
        )
        print(
            f"expectations matched="
            f"{artifact.expectation_totals.matched}/"
            f"{artifact.expectation_totals.evaluated}"
        )
        print(f"summary artifacts: {out_dir}")
        print(artifact.disclaimer)
    else:
        print(f"wrote summary artifacts under {out_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
