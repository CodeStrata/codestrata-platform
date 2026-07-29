#!/usr/bin/env python3
"""Canonical release / maintainer verification for codestrata-platform.

Runs the supported product quality gates from the monorepo root. Does not push,
publish, or create remotes.

Default steps:
  1. security_check
  2. ruff check . (Community Engine tree)
  3. mypy engine/src
  4. pytest -m "not network"
  5. export-public-repos
  6. validate-public-exports (--skip-install by default)

Optional:
  --full-export-install   run export validation with fresh-venv Engine smoke
  --with-clean-install    run packaging clean-install smoke
  --with-acceptance       run ``codestrata acceptance run`` (live / heavy; requires
                          CODESTRATA_MAINTAINER_CLI)
  --skip-export / --skip-tests / --skip-lint  omit selected steps

Examples:
  python scripts/verify_release.py
  python scripts/verify_release.py --full-export-install
  python scripts/verify_release.py --skip-export
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"


@dataclass(frozen=True)
class Step:
    name: str
    argv: list[str]
    cwd: Path = ROOT


def _python() -> str:
    return sys.executable


def _run(step: Step) -> int:
    print(f"\n==> {step.name}")
    print("    " + " ".join(step.argv))
    completed = subprocess.run(step.argv, cwd=step.cwd, check=False)
    if completed.returncode != 0:
        print(f"FAIL: {step.name} (exit {completed.returncode})")
        return completed.returncode
    print(f"OK:   {step.name}")
    return 0


def _require_tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is None:
        # Prefer the active interpreter's module form.
        return None
    return path


def build_steps(args: argparse.Namespace) -> list[Step]:
    py = _python()
    steps: list[Step] = [
        Step(
            "security_check",
            [py, str(ROOT / "scripts" / "security_check.py")],
        ),
    ]

    if not args.skip_lint:
        ruff = _require_tool("ruff")
        # Community Engine release gate (matches engine/CONTRIBUTING.md).
        # Do not lint the full monorepo root: Platform/historical debt is out of
        # Community Engine release scope.
        if ruff:
            steps.append(Step("ruff", [ruff, "check", "."], cwd=ENGINE))
        else:
            steps.append(Step("ruff", [py, "-m", "ruff", "check", "."], cwd=ENGINE))

        steps.append(Step("mypy", [py, "-m", "mypy", "src"], cwd=ENGINE))

    if not args.skip_tests:
        steps.append(
            Step(
                "pytest",
                [py, "-m", "pytest", "-m", "not network", "-q"],
            )
        )

    if not args.skip_export:
        steps.append(
            Step(
                "export_public_repos",
                [py, str(ROOT / "scripts" / "export-public-repos.py")],
            )
        )
        validate_argv = [
            py,
            str(ROOT / "scripts" / "validate-public-exports.py"),
        ]
        if not args.full_export_install:
            validate_argv.append("--skip-install")
        steps.append(Step("validate_public_exports", validate_argv))

    if args.with_clean_install:
        steps.append(
            Step(
                "clean_install_smoke",
                [py, str(ROOT / "scripts" / "clean_install_smoke.py")],
            )
        )

    if args.with_acceptance:
        codestrata = _require_tool("codestrata")
        if codestrata:
            steps.append(
                Step(
                    "acceptance_run",
                    [codestrata, "acceptance", "run"],
                )
            )
        else:
            steps.append(
                Step(
                    "acceptance_run",
                    [py, "-m", "codestrata", "acceptance", "run"],
                )
            )

    return steps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the current codestrata-platform tree is release-ready "
            "(security, lint, tests, public export)."
        )
    )
    parser.add_argument(
        "--skip-lint",
        action="store_true",
        help="Skip ruff and mypy.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip pytest.",
    )
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Skip export + validate-public-exports.",
    )
    parser.add_argument(
        "--full-export-install",
        action="store_true",
        help=(
            "Run validate-public-exports without --skip-install (fresh venv Engine smoke; slower)."
        ),
    )
    parser.add_argument(
        "--with-clean-install",
        action="store_true",
        help="Also run packaging clean-install smoke.",
    )
    parser.add_argument(
        "--with-acceptance",
        action="store_true",
        help="Also run codestrata acceptance run (live / heavy).",
    )
    args = parser.parse_args(argv)

    steps = build_steps(args)
    print(f"verify_release: {len(steps)} step(s) from {ROOT}")
    for step in steps:
        code = _run(step)
        if code != 0:
            print("\nverify_release: FAILED")
            return code

    print("\nverify_release: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
