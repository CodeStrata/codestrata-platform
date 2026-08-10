"""Representative repository selection for Slice 17.19."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import (
    ASSESSMENTS_RELATIVE,
    ASSESSMENT_JSON,
    CATALOG_RELATIVE,
    REPRESENTATIVE_CATALOG_IDS,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    github_artifact_folder,
    hard_defect,
    load_json,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)

SELECTION_REASONS: dict[str, str] = {
    "flask": "small Python web framework",
    "express": "small Node HTTP framework",
    "juice-shop": "OWASP security-rich JS/TS app",
    "spring-petclinic": "Java/Spring sample web app",
    "vite": "medium TypeScript frontend toolchain",
    "nodegoat": "OWASP Node security app (mixed security posture vs juice-shop)",
}


def resolve_current_assessment_dir(
    monorepo: Path,
    catalog_id: str,
    *,
    preferred_folder: str | None = None,
) -> Path | None:
    """Resolve ``assessments/*/current`` for a catalog id via assessment.json."""

    root = monorepo / ASSESSMENTS_RELATIVE
    if not root.is_dir():
        return None

    if preferred_folder:
        preferred = root / preferred_folder / "current"
        if (preferred / ASSESSMENT_JSON).is_file():
            return preferred

    catalog_id_l = catalog_id.strip().lower()
    exact: Path | None = None
    fuzzy: Path | None = None
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        current = child / "current"
        manifest_path = current / ASSESSMENT_JSON
        if not manifest_path.is_file():
            continue
        try:
            manifest = load_json(manifest_path)
        except (OSError, TypeError, json.JSONDecodeError, ValueError):
            continue
        repo_id = str(manifest.get("repository_id") or "").strip().lower()
        repo_name = str(
            manifest.get("repository") or manifest.get("repository_name") or ""
        ).strip().lower()
        folder = child.name.lower()
        if catalog_id_l == repo_name or repo_id == preferred_folder or folder.endswith(
            f"-{catalog_id_l}"
        ):
            exact = current
            break
        if fuzzy is None and (
            catalog_id_l == folder
            or folder.endswith(f"-{catalog_id_l}")
            or catalog_id_l.replace("-", "") in folder.replace("-", "")
        ):
            fuzzy = current
    return exact or fuzzy


def _catalog_by_id(monorepo: Path) -> dict[str, dict[str, Any]]:
    doc = load_json(monorepo / CATALOG_RELATIVE)
    out: dict[str, dict[str, Any]] = {}
    for item in doc.get("repositories") or []:
        if isinstance(item, dict) and item.get("id"):
            out[str(item["id"])] = item
    return out


def select_repositories(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = ["bounded_representative_subset"]

    catalog = _catalog_by_id(monorepo)
    selected: list[dict[str, Any]] = []
    missing: list[str] = []

    for catalog_id in REPRESENTATIVE_CATALOG_IDS:
        entry = catalog.get(catalog_id)
        ok = entry is not None
        checks.append(
            check(
                f"selection:catalog_id:{catalog_id}",
                ok,
                SELECTION_REASONS.get(catalog_id, catalog_id),
                "selection",
            )
        )
        if not ok:
            missing.append(catalog_id)
            defects.append(
                hard_defect(
                    "missing_catalog_id",
                    f"selection:catalog_id:{catalog_id}",
                    "present",
                    "absent",
                )
            )
            continue

        github = str(entry.get("github_repository") or "")
        expected_folder = github_artifact_folder(github) if github else ""
        current = resolve_current_assessment_dir(
            monorepo,
            catalog_id,
            preferred_folder=expected_folder or None,
        )

        present = current is not None and (current / ASSESSMENT_JSON).is_file()
        checks.append(
            check(
                f"selection:current_assessment:{catalog_id}",
                present,
                str(current.relative_to(monorepo)) if present and current else "absent",
                "selection",
            )
        )
        if not present:
            defects.append(
                hard_defect(
                    "missing_assessment",
                    f"selection:current_assessment:{catalog_id}",
                    "current/assessment.json",
                    "absent",
                )
            )

        artifact_folder = current.parent.name if current is not None else expected_folder
        selected.append(
            {
                "catalog_id": catalog_id,
                "project_name": str(entry.get("project_name") or catalog_id),
                "github_repository": github,
                "language_group": entry.get("language_group"),
                "qualified_revision": (entry.get("qualified_revision") or {}),
                "reason": SELECTION_REASONS[catalog_id],
                "artifact_folder": artifact_folder,
                "current_relative": (
                    str(current.relative_to(monorepo)) if present and current else None
                ),
            }
        )

    all_six = len(selected) == 6 and not missing and all(s.get("current_relative") for s in selected)
    checks.append(
        check(
            "selection:exactly_six",
            all_six,
            f"selected={len(selected)};missing={missing}",
            "selection",
        )
    )
    if not all_six and not defects:
        defects.append(
            hard_defect(
                "selection_incomplete",
                "selection:exactly_six",
                "6",
                str(len(selected)),
            )
        )

    summary: dict[str, Any] = {
        "catalog_ids": list(REPRESENTATIVE_CATALOG_IDS),
        "selected": [
            {
                "catalog_id": s["catalog_id"],
                "github_repository": s["github_repository"],
                "artifact_folder": s["artifact_folder"],
                "current_relative": s["current_relative"],
                "reason": s["reason"],
            }
            for s in selected
        ],
        "count": len(selected),
        "bounded_representative_subset": True,
    }
    return checks, defects, summary, limitations
