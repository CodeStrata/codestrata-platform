"""CLI entry: ``python -m infrastructure.verification``."""

from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.verification.runner import (
    run_platform_deployment_foundation_verification,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SV.9 Platform Deployment Foundation Verification",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--skip-opentofu-cli",
        action="store_true",
        help="Skip tofu fmt/init/validate even if tofu is available.",
    )
    args = parser.parse_args(argv)

    report = run_platform_deployment_foundation_verification(
        output_dir=args.output_dir,
        run_opentofu_cli=not args.skip_opentofu_cli,
    )
    print(
        f"SV.9 platform deployment foundation verification: "
        f"{'PASS' if report.ok else 'FAIL'}"
    )
    print(f"verdict: {report.verdict}")
    print(f"opentofu_validation_status: {report.opentofu_validation_status}")
    print(f"terraform_tool_status: {report.terraform_tool_status}")
    if report.defects:
        print(f"defects: {', '.join(report.defects[:8])}")
    out = (
        (args.output_dir or Path("infrastructure/reports/verification"))
        / "platform-deployment-foundation-verification.json"
    )
    print(f"report: {out}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
