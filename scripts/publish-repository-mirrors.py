#!/usr/bin/env python3
"""Publish staged CodeStrata repository mirrors to GitHub.

Defaults to dry-run. Real pushes require both ``--push`` and ``--confirm``.
Never creates GitHub repositories, never force-pushes, never tags/releases.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from release.inventory import load_export_manifest  # noqa: E402
from release.mirror_publish import (  # noqa: E402
    PublishError,
    build_plan,
    current_source_commit,
    execute_plan,
    select_exports,
    source_is_clean,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "public-export-manifest.yaml",
    )
    parser.add_argument(
        "--staging",
        type=Path,
        default=None,
        help="Staging root (default: manifest staging_directory)",
    )
    parser.add_argument(
        "--repo",
        action="append",
        dest="repos",
        help="Publish only this export/destination name (repeatable).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="publish_all",
        help="Select every export in the manifest (still dry-run unless --push).",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Perform a real push (also requires --confirm). Default: dry-run.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Acknowledge a non-dry-run publish. Required with --push.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=argparse.SUPPRESS,  # rejected explicitly
    )
    args = parser.parse_args(argv)

    if args.force:
        print("ERROR: force-push is forbidden by policy", file=sys.stderr)
        return 2
    if args.push and not args.confirm:
        print("ERROR: --push requires --confirm", file=sys.stderr)
        return 2
    if args.confirm and not args.push:
        print("ERROR: --confirm is only valid with --push", file=sys.stderr)
        return 2

    dry_run = not args.push
    try:
        if not source_is_clean(ROOT):
            raise PublishError("source working tree is dirty; commit or stash first")
        source_commit = current_source_commit(ROOT)
        manifest = load_export_manifest(ROOT)
        staging_root = args.staging or (
            ROOT / str(manifest.get("staging_directory", ".export-staging"))
        )
        exports = select_exports(
            manifest,
            repos=args.repos,
            publish_all=bool(args.publish_all),
        )

        plans = [
            build_plan(
                root=ROOT,
                export=item,
                staging_root=staging_root,
                source_commit=source_commit,
                dry_run=dry_run,
            )
            for item in exports
        ]

        print(
            f"mode={'DRY-RUN' if dry_run else 'PUSH'} "
            f"source_commit={source_commit} count={len(plans)}"
        )
        for plan in plans:
            print(
                f"- {plan.full_name} visibility={plan.visibility} "
                f"branch=main action={plan.action} "
                f"staging={plan.staging_dir.name} "
                f"source_commit={plan.source_commit}"
            )
            for note in plan.notes:
                print(f"    note: {note}")

        if dry_run:
            print("Dry-run complete; no remotes were modified.")
            return 0

        work_root = Path(tempfile.mkdtemp(prefix="codestrata-mirror-publish-"))
        try:
            for plan in plans:
                # Rebuild non-dry action names for execution.
                plan.action = "bootstrap" if plan.action.endswith("bootstrap") else "update"
                print(f"publishing {plan.full_name} ({plan.action})…")
                execute_plan(plan, work_root=work_root, dry_run=False)
                print(f"OK: {plan.full_name}")
        finally:
            shutil.rmtree(work_root, ignore_errors=True)
        print("Publish complete.")
        return 0
    except PublishError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
