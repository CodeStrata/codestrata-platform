"""CLI for Slice 12.8 verification."""

from __future__ import annotations

from verification.repository_export_targets.runner import run


def main() -> int:
    report = run()
    print(
        f"{report.schema_name}:{report.schema_version} "
        f"verdict={report.verdict} "
        f"checks={report.total_checks} failed={report.failed_checks}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
