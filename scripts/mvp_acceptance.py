#!/usr/bin/env python3
"""Run the live MVP acceptance harness (Phase 5.13).

Equivalent to ``codestrata acceptance run``. Uses real repositories — not report fixtures.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine" / "src"))

from codestrata.application.acceptance import run_mvp_acceptance  # noqa: E402


def main() -> int:
    output = ROOT / "reports" / "mvp-acceptance"
    result = run_mvp_acceptance(
        output_directory=output,
        config_path=ROOT / "codestrata.toml",
    )
    print(f"mvp acceptance: {'PASS' if result.ok else 'FAIL'}")
    print(f"summary: {output / 'summary.json'}")
    print(f"markdown: {output / 'summary.md'}")
    for repo in result.repositories:
        print(
            f"  {repo.repository}: ok={repo.ok} onboard={repo.onboarding_status} "
            f"findings={repo.findings} chunks={repo.chunks} "
            f"validate={repo.report_validation} qa={repo.question_answer} "
            f"mcp={repo.mcp_health} determinism={repo.determinism} "
            f"({repo.elapsed_ms:.0f} ms)"
        )
        if repo.failure_reason:
            print(f"    reason: {repo.failure_reason}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
