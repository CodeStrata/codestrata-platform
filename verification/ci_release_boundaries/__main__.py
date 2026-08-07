"""CLI entry: python -m verification.ci_release_boundaries"""

from __future__ import annotations

import sys

from verification.ci_release_boundaries.runner import run


def main(argv: list[str] | None = None) -> int:
    _ = argv
    report = run()
    print(
        f"{report.schema_name}:{report.schema_version} "
        f"verdict={report.verdict} "
        f"checks={report.total_checks} failed={report.failed_checks}"
    )
    if report.failed_checks > 0 or report.verdict == "FAIL":
        for c in report.checks:
            if not c.ok:
                print(f"  FAIL {c.name}: {c.detail}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
