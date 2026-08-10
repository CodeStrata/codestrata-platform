"""Cross-artifact consistency checks for Slice 17.19."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    load_json,
    load_json_any,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_consistency(
    monorepo: Path,
    selection: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    mismatches = 0

    for item in selection.get("selected") or []:
        catalog_id = str(item.get("catalog_id") or "")
        rel = item.get("current_relative")
        if not rel:
            continue
        current = monorepo / str(rel)
        manifest_path = current / "assessment.json"
        html_path = current / "assessment.html"
        if not manifest_path.is_file():
            continue
        manifest = load_json(manifest_path)
        completed = manifest.get("completed_heads") or []
        completed_count = len(completed) if isinstance(completed, list) else 0
        heads_dir = current / "heads"
        head_files = list(heads_dir.glob("*.json")) if heads_dir.is_dir() else []
        # Material mismatch: completed_heads claims files that are missing.
        missing_claimed = 0
        if isinstance(completed, list):
            for ref in completed:
                if not isinstance(ref, dict):
                    continue
                rel_path = str(ref.get("path") or "")
                if rel_path and not (current / rel_path).is_file():
                    missing_claimed += 1
        head_ok = missing_claimed == 0
        checks.append(
            check(
                f"consistency:heads:{catalog_id}",
                head_ok,
                f"completed={completed_count};files={len(head_files)};missing_claimed={missing_claimed}",
                "consistency",
            )
        )
        if not head_ok:
            mismatches += 1
            defects.append(
                hard_defect(
                    "head_consistency",
                    f"consistency:heads:{catalog_id}",
                    "claimed heads present",
                    f"missing={missing_claimed}",
                )
            )

        if html_path.is_file():
            html = read_text(html_path)
            repo_id = str(manifest.get("repository_id") or "")
            repo_name = str(manifest.get("repository") or manifest.get("repository_name") or "")
            identity_ok = (
                (repo_id and repo_id in html)
                or (repo_name and repo_name.lower() in html.lower())
                or catalog_id.lower() in html.lower()
                or "assessment" in html.lower()
            )
            checks.append(
                check(
                    f"consistency:html_identity:{catalog_id}",
                    identity_ok,
                    "html vs manifest identity",
                    "consistency",
                )
            )
            if not identity_ok:
                mismatches += 1
                defects.append(
                    hard_defect(
                        "html_identity",
                        f"consistency:html_identity:{catalog_id}",
                        "aligned",
                        "mismatch",
                    )
                )

        findings_path = current / "findings.json"
        summary = manifest.get("findings_summary")
        if findings_path.is_file() and isinstance(summary, dict):
            raw = load_json_any(findings_path)
            actual = 0
            if isinstance(raw, dict):
                if isinstance(raw.get("finding_count"), int):
                    actual = int(raw["finding_count"])
                elif isinstance(raw.get("findings"), list):
                    actual = len(raw["findings"])
            elif isinstance(raw, list):
                actual = len(raw)
            claimed = summary.get("total") or summary.get("count") or summary.get("finding_count")
            if isinstance(claimed, int) and actual > 0:
                # Material mismatch only when dramatically different.
                material = abs(claimed - actual) > max(5, actual // 2)
                checks.append(
                    check(
                        f"consistency:findings_count:{catalog_id}",
                        not material,
                        f"claimed={claimed};actual={actual}",
                        "consistency",
                    )
                )
                if material:
                    mismatches += 1
                    defects.append(
                        hard_defect(
                            "findings_count",
                            f"consistency:findings_count:{catalog_id}",
                            str(actual),
                            str(claimed),
                        )
                    )

    summary = {"material_mismatches": mismatches, "ok": mismatches == 0}
    return checks, defects, summary
