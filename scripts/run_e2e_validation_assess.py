#!/usr/bin/env python3
"""Run a deterministic sample assessment and preserve artifacts for E2E review.

Does not change assessment logic. Invokes the installed ``codestrata`` CLI, then
copies HTML/JSON/graphs into ``reports/validation/<repo>/``.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "test-fixtures" / "sample-js-app"
_PRESERVE = ROOT / "scripts" / "preserve_validation_artifacts.py"


def _load_preserve():
    spec = importlib.util.spec_from_file_location("preserve_validation_artifacts", _PRESERVE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {_PRESERVE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assess a fixture repo and preserve outputs under reports/validation/."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=DEFAULT_FIXTURE,
        help=f"Repository to assess (default: {DEFAULT_FIXTURE})",
    )
    parser.add_argument(
        "--codestrata",
        default="codestrata",
        help="codestrata executable (default: codestrata on PATH)",
    )
    parser.add_argument(
        "--repository-name",
        help="Validation folder name (default: repo directory name)",
    )
    args = parser.parse_args(argv)

    repo = args.repo.expanduser().resolve()
    if not repo.is_dir():
        print(f"Error: repository not found: {repo}", file=sys.stderr)
        return 1

    name = args.repository_name or repo.name
    with tempfile.TemporaryDirectory(prefix="codestrata-validation-") as tmp:
        output = Path(tmp) / "reports"
        command = [
            args.codestrata,
            "assess",
            "--repo",
            str(repo),
            "--output",
            str(output),
            "--no-ai",
            "--quiet",
        ]
        print("Running:", " ".join(command))
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            print(f"Error: assess exited {completed.returncode}", file=sys.stderr)
            return completed.returncode

        preserve = _load_preserve()
        run = preserve.find_latest_assess_run(output)
        if run is None:
            print("Error: assess produced no report.html", file=sys.stderr)
            return 1

        stamped = preserve.preserve_validation_artifacts(
            run,
            repository_name=name,
            validation_root=ROOT / "reports" / "validation",
        )
        print(f"Review HTML: {stamped / 'report.html'}")
        print(f"Stable latest: reports/validation/{name}/latest/report.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
