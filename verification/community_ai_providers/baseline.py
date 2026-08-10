"""--no-ai baseline artifacts and zero provider-call markers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import WORK_ASSESS_OUT
from verification.community_ai_providers.helpers import (
    PROVIDER_CALL_MARKERS,
    artifact_dir,
    check,
    hard_defect,
    read_text,
)
from verification.community_ai_providers.models import CheckResult, Defect


def check_baseline(
    monorepo: Path,
    *,
    repositories: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    rows: list[dict[str, Any]] = []

    work_no_ai_root = WORK_ASSESS_OUT / "no-ai"
    work_no_ai_present = work_no_ai_root.is_dir()

    for item in repositories.get("selected") or []:
        catalog_id = str(item.get("catalog_id") or "")
        work_path = artifact_dir(item, "work_no_ai", monorepo=monorepo)
        github_path = artifact_dir(item, "github_current", monorepo=monorepo)
        baseline_dir = work_path or github_path
        has_findings = bool(
            baseline_dir and (baseline_dir / "findings.json").is_file()
        )
        has_assessment = bool(
            baseline_dir and (baseline_dir / "assessment.json").is_file()
        )
        advisor_required = False
        has_advisor = bool(
            baseline_dir and (baseline_dir / "advisor.json").is_file()
        )

        checks.append(
            check(
                f"baseline:{catalog_id}_present",
                has_findings or has_assessment,
                f"dir={'work_no_ai' if work_path else 'github_current' if github_path else 'none'}",
                "baseline",
            )
        )
        if not (has_findings or has_assessment):
            defects.append(
                hard_defect(
                    "missing_baseline",
                    f"baseline:{catalog_id}_present",
                    "findings or assessment",
                    "absent",
                )
            )

        checks.append(
            check(
                f"baseline:{catalog_id}_advisor_not_required",
                True,
                f"advisor_present={has_advisor} required={advisor_required}",
                "baseline",
            )
        )

        marker_hits: list[str] = []
        if baseline_dir:
            for log_name in ("assess.log", "stdout.log", "stderr.log", "run.log"):
                log_path = baseline_dir / log_name
                if not log_path.is_file():
                    continue
                text = read_text(log_path)
                for pattern in PROVIDER_CALL_MARKERS:
                    if pattern.search(text):
                        marker_hits.append(f"{log_name}:{pattern.pattern}")
        zero_markers = not marker_hits
        checks.append(
            check(
                f"baseline:{catalog_id}_zero_provider_markers",
                zero_markers,
                "no logs" if baseline_dir is None else f"hits={len(marker_hits)}",
                "baseline",
            )
        )
        if marker_hits:
            defects.append(
                hard_defect(
                    "provider_call_in_no_ai_log",
                    f"baseline:{catalog_id}_zero_provider_markers",
                    "zero",
                    ",".join(marker_hits[:5]),
                )
            )

        rows.append(
            {
                "catalog_id": catalog_id,
                "baseline_source": "work_no_ai" if work_path else ("github_current" if github_path else None),
                "has_findings": has_findings,
                "has_assessment": has_assessment,
                "advisor_required": False,
                "advisor_present": has_advisor,
                "provider_call_markers": marker_hits,
            }
        )

    summary = {
        "work_no_ai_root_present": work_no_ai_present,
        "repositories": rows,
        "advisor_json_required_for_baseline": False,
        "cli_flags": "--no-ai (NOT --ai); --with-ai optional",
    }
    return checks, defects, summary
