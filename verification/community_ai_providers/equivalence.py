"""Compare no-ai vs bedrock finding ID sets when both exist."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import WORK_ASSESS_OUT
from verification.community_ai_providers.helpers import (
    artifact_dir,
    check,
    finding_ids_from_findings_json,
    hard_defect,
)
from verification.community_ai_providers.models import CheckResult, Defect


def check_equivalence(
    monorepo: Path,
    *,
    repositories: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    comparisons: list[dict[str, Any]] = []

    for item in repositories.get("selected") or []:
        catalog_id = str(item.get("catalog_id") or "")
        no_ai = artifact_dir(item, "work_no_ai", monorepo=monorepo)
        bedrock = artifact_dir(item, "work_bedrock", monorepo=monorepo)

        if no_ai is None:
            cand = WORK_ASSESS_OUT / "no-ai" / catalog_id
            if (cand / "findings.json").is_file():
                no_ai = cand
        if bedrock is None:
            cand = WORK_ASSESS_OUT / "bedrock" / catalog_id
            if (cand / "findings.json").is_file():
                bedrock = cand

        if not (no_ai and bedrock):
            checks.append(
                check(
                    f"equivalence:{catalog_id}_skipped",
                    True,
                    "both baselines not present under /tmp/sv17-20-work",
                    "equivalence",
                )
            )
            comparisons.append(
                {
                    "catalog_id": catalog_id,
                    "compared": False,
                    "reason": "missing_pair",
                }
            )
            continue

        no_ai_findings = no_ai / "findings.json"
        bedrock_findings = bedrock / "findings.json"
        if not (no_ai_findings.is_file() and bedrock_findings.is_file()):
            checks.append(
                check(
                    f"equivalence:{catalog_id}_skipped",
                    True,
                    "findings.json missing on one side",
                    "equivalence",
                )
            )
            comparisons.append(
                {
                    "catalog_id": catalog_id,
                    "compared": False,
                    "reason": "missing_findings",
                }
            )
            continue

        ids_a = finding_ids_from_findings_json(no_ai_findings)
        ids_b = finding_ids_from_findings_json(bedrock_findings)
        only_a = sorted(ids_a - ids_b)
        only_b = sorted(ids_b - ids_a)
        equal = not only_a and not only_b
        checks.append(
            check(
                f"equivalence:{catalog_id}_finding_ids",
                equal,
                f"no_ai={len(ids_a)} bedrock={len(ids_b)} delta={len(only_a)+len(only_b)}",
                "equivalence",
            )
        )
        if not equal:
            defects.append(
                hard_defect(
                    "deterministic_finding_id_delta",
                    f"equivalence:{catalog_id}_finding_ids",
                    "identical finding ID sets",
                    f"only_no_ai={only_a[:10]} only_bedrock={only_b[:10]}",
                )
            )
        comparisons.append(
            {
                "catalog_id": catalog_id,
                "compared": True,
                "equal": equal,
                "no_ai_count": len(ids_a),
                "bedrock_count": len(ids_b),
                "only_no_ai_sample": only_a[:5],
                "only_bedrock_sample": only_b[:5],
                "advisor_narrative_differences_allowed": True,
            }
        )

    summary = {
        "comparisons": comparisons,
        "material_finding_id_delta_is_defect": True,
        "advisor_differences_allowed": True,
    }
    return checks, defects, summary
