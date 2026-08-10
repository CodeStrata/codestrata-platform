"""Negative scenario matrix for Slice 17.19 (A–Z)."""

from __future__ import annotations

from pathlib import Path

from verification.community_assessment_engineering_intelligence.helpers import check
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_scenarios(
    monorepo: Path,
    *,
    flags: dict[str, bool],
) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    scenarios: list[tuple[str, str, bool]] = [
        ("A", "assessment.json becomes giant duplicate of heads", flags.get("manifest_lightweight", False)),
        ("B", "supported head silently disappears", flags.get("heads_represented", False)),
        ("C", "HTML contradicts head JSON", flags.get("consistency_ok", False)),
        ("D", "finding lacks evidence", flags.get("evidence_ok", False)),
        ("E", "evidence reference broken", flags.get("evidence_ok", False)),
        ("F", "insufficient evidence becomes definitive claim", flags.get("insufficient_honest", False)),
        ("G", "AI narrative presented as deterministic fact", flags.get("ai_boundary_ok", False)),
        ("H", "one head failure corrupts whole assessment", flags.get("failure_isolated", False)),
        ("I", "failed assessment replaces current", flags.get("failed_assessment_no_promote", False)),
        ("J", "EIR generated as ordinary single-repo assessment", flags.get("eir_portfolio_level", False)),
        ("K", "EIR secretly rescans repositories", flags.get("eir_no_rescan", False)),
        ("L", "EIR conclusion cannot trace to repositories", flags.get("eir_traceable", False)),
        ("M", "portfolio counts incorrect", flags.get("aggregation_ok", False)),
        ("N", "mixed evidence flattened into universal conclusion", flags.get("mixed_evidence_ok", False)),
        ("O", "membership changes create unrelated portfolio identity", flags.get("membership_stable", False)),
        ("P", "failed EIR replaces current", flags.get("failed_eir_no_promote", False)),
        ("Q", "third lifecycle version retained", flags.get("two_slot_lifecycle", False)),
        ("R", "local path appears in public/customer report", flags.get("privacy_ok", False)),
        ("S", "secret/token appears in report", flags.get("privacy_ok", False)),
        ("T", "report artifacts enter Data Lake", flags.get("no_reports_in_lake", False)),
        ("U", "full 22-repo release corpus starts", flags.get("no_full_22", False)),
        ("V", "provider E2E starts", flags.get("no_provider_e2e", False)),
        ("W", "VS Code marketplace publish starts", flags.get("no_vscode_publish", False)),
        ("X", "Community Status feature starts", flags.get("no_status_api", False)),
        ("Y", "Slice 17.21 starts", flags.get("no_17_21", False)),
        ("Z", "verifier nondeterministic", flags.get("deterministic", False)),
    ]
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: dict[str, bool] = {}
    for letter, detail, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(check(f"scenario:{letter}", bool(ok), detail, "scenarios"))
        if not ok:
            defects.append(
                Defect(
                    classification=f"scenario_{letter}",
                    check_id=f"scenario:{letter}",
                    expected="pass",
                    detail=detail,
                )
            )
    _ = monorepo
    return checks, defects, results
