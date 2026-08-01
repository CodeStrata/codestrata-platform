#!/usr/bin/env python3
"""Developer-facing multi-repository validation CLI (not the public customer CLI).

Examples::

    python -m validation.run_validation --list
    python -m validation.run_validation --local-only
    python -m validation.run_validation --repository local-sample-js --keep-results
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from validation.models import ValidationVerdict
from validation.paths import RESULTS_DIR, VALIDATION_ROOT
from validation.registry import RegistryError, filter_repositories, load_all_repositories
from validation.runner import run_validation_suite
from validation.summary import build_validation_summary, summary_to_safe_dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validation.run_validation",
        description="Run CodeStrata multi-repository assessment validation harness.",
    )
    parser.add_argument(
        "--repository",
        action="append",
        dest="repositories",
        default=[],
        help="Repository id to run (repeatable).",
    )
    parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        default=[],
        help="Only repositories with this tag (repeatable).",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Run only local fixture repositories (skip remotes).",
    )
    parser.add_argument(
        "--include-remote",
        action="store_true",
        help="Include pinned remote repositories (network required).",
    )
    parser.add_argument(
        "--keep-results",
        action="store_true",
        help="Retain temporary clones and assessment outputs.",
    )
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="Skip writing permanent per-repository validation records.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for assessment outputs (default: temp, or results/ with --keep-results).",
    )
    parser.add_argument(
        "--records-dir",
        type=Path,
        default=None,
        help="Directory for permanent validation records (default: engine/validation/results/).",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first FAIL or ERROR.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List repository definitions and exit.",
    )
    parser.add_argument(
        "--json-summary",
        action="store_true",
        help="Print a minimal JSON summary to stdout.",
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help=(
            "Build Slice 4.12 validation-summary.json/.md from existing records "
            "without running assessments."
        ),
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="With --summarize, print a short human summary.",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="With --summarize, write JSON artifact only.",
    )
    parser.add_argument(
        "--markdown-only",
        action="store_true",
        help="With --summarize, write Markdown artifact only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.summarize:
        from validation.generate_summary import main as summarize_main

        summarize_argv: list[str] = []
        if args.records_dir is not None:
            summarize_argv.extend(["--records-dir", str(args.records_dir)])
        if args.output_dir is not None:
            summarize_argv.extend(["--output-dir", str(args.output_dir)])
        for repo in args.repositories:
            summarize_argv.extend(["--repository", repo])
        for tag in args.tags:
            summarize_argv.extend(["--tag", tag])
        if args.local_only:
            summarize_argv.append("--local-only")
        if args.include_remote:
            summarize_argv.append("--include-remote")
        if args.print_summary:
            summarize_argv.append("--print-summary")
        if args.json_only:
            summarize_argv.append("--json-only")
        if args.markdown_only:
            summarize_argv.append("--markdown-only")
        return summarize_main(summarize_argv)

    try:
        definitions = load_all_repositories()
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.list:
        if not definitions:
            print("No repository definitions found under validation/repositories/")
            return 0
        for item in definitions:
            status = "enabled" if item.enabled else "disabled"
            print(
                f"{item.repository_id}\t{item.source_type.value}\t{status}\t"
                f"{item.display_name}\ttags={','.join(item.tags) or '-'}"
            )
        return 0

    try:
        selected = filter_repositories(
            definitions,
            repository_ids=set(args.repositories) if args.repositories else None,
            tags=set(args.tags) if args.tags else None,
            local_only=args.local_only,
            include_remote=args.include_remote,
        )
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    # When specific remotes were requested without --include-remote, still load
    # them into the suite so the runner can emit SKIPPED rather than silently omit.
    if args.repositories and not args.include_remote and not args.local_only:
        requested = {item for item in definitions if item.repository_id in set(args.repositories)}
        merged = {item.repository_id: item for item in selected}
        for item in requested:
            merged.setdefault(item.repository_id, item)
        selected = tuple(merged[rid] for rid in sorted(merged))

    if not selected:
        # Default: all local (and remotes only if include_remote).
        selected = filter_repositories(
            definitions,
            local_only=True if not args.include_remote else False,
            include_remote=args.include_remote,
        )

    if not selected:
        print("No repositories selected.", file=sys.stderr)
        return 2

    records_root = args.records_dir if args.records_dir is not None else RESULTS_DIR
    records_root.mkdir(parents=True, exist_ok=True)

    if args.output_dir is not None:
        output_root = args.output_dir
        output_root.mkdir(parents=True, exist_ok=True)
        cleanup_output = False
    elif args.keep_results:
        output_root = RESULTS_DIR
        output_root.mkdir(parents=True, exist_ok=True)
        cleanup_output = False
    else:
        output_root = Path(tempfile.mkdtemp(prefix="codestrata-validation-out-"))
        cleanup_output = True

    try:
        results = run_validation_suite(
            selected,
            output_root=output_root,
            keep_results=args.keep_results,
            include_remote=args.include_remote,
            local_only=args.local_only,
            fail_fast=args.fail_fast,
            validation_root=VALIDATION_ROOT,
            records_root=records_root,
            record_results=not args.no_record,
        )
    finally:
        if cleanup_output and output_root.exists() and not args.keep_results:
            # Per-repo cleanup already happened; remove empty temp root.
            try:
                output_root.rmdir()
            except OSError:
                pass

    summary = build_validation_summary(results)
    if args.json_summary:
        print(json.dumps(summary_to_safe_dict(summary), indent=2, sort_keys=True))
    else:
        _print_human_summary(summary)
        if not args.no_record:
            print(f"validation records: {records_root}")

    if summary.failed or summary.errors:
        return 1
    return 0


def _print_human_summary(summary) -> None:
    print(
        f"repositories={summary.total_repositories} "
        f"passed={summary.passed} failed={summary.failed} "
        f"errors={summary.errors} skipped={summary.skipped}"
    )
    print(
        f"expectations matched={summary.matched_expectations}/"
        f"{summary.total_expectations}"
    )
    if summary.mismatches_by_area:
        print("mismatches by area:")
        for area, count in summary.mismatches_by_area.items():
            print(f"  {area}: {count}")
    for result in summary.results:
        line = f"  [{result.verdict.value}] {result.repository_id}"
        if result.verdict == ValidationVerdict.ERROR and result.error_message:
            line += f" — {result.error_message}"
        if result.verdict == ValidationVerdict.SKIPPED and result.skip_reason:
            line += f" — {result.skip_reason}"
        print(line)
        for mismatch in result.mismatches:
            print(
                f"    - area={mismatch.assessment_area} "
                f"expected={mismatch.expectation} actual={mismatch.actual} "
                f"({mismatch.diagnostic})"
            )


if __name__ == "__main__":
    raise SystemExit(main())
