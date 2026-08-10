"""Select representative repositories for Slice 17.20."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import (
    ASSESSMENTS_RELATIVE,
    CATALOG_RELATIVE,
    REPRESENTATIVE_PREFERRED,
    WORK_ASSESS_OUT,
)
from verification.community_ai_providers.helpers import (
    check,
    github_artifact_folder,
    hard_defect,
    load_json,
)
from verification.community_ai_providers.models import CheckResult, Defect

SELECTION_REASONS: dict[str, str] = {
    "flask": "small Python web framework — quick provider iteration",
    "juice-shop": "OWASP security-rich JS/TS app — meaningful enrichment context",
    "express": "small Node HTTP framework — alternate stack if juice-shop absent",
}


def _catalog_by_id(monorepo: Path) -> dict[str, dict[str, Any]]:
    doc = load_json(monorepo / CATALOG_RELATIVE)
    out: dict[str, dict[str, Any]] = {}
    for item in doc.get("repositories") or []:
        if isinstance(item, dict) and item.get("id"):
            out[str(item["id"])] = item
    return out


def resolve_assessment_dirs(
    monorepo: Path,
    catalog_id: str,
    *,
    github_repository: str | None = None,
) -> dict[str, Path | None]:
    """Resolve github-* current dirs and optional /tmp/sv17-20-work assess-out."""

    assessments = monorepo / ASSESSMENTS_RELATIVE
    folder = (
        github_artifact_folder(github_repository)
        if github_repository
        else None
    )
    github_current: Path | None = None
    if folder:
        candidate = assessments / folder / "current"
        if (candidate / "findings.json").is_file() or (
            candidate / "assessment.json"
        ).is_file():
            github_current = candidate
    if github_current is None and assessments.is_dir():
        needle = catalog_id.lower()
        for child in sorted(assessments.iterdir()):
            if not child.is_dir():
                continue
            if needle in child.name.lower():
                current = child / "current"
                if (current / "findings.json").is_file() or (
                    current / "assessment.json"
                ).is_file():
                    github_current = current
                    break

    def _if_present(path: Path) -> Path | None:
        if (path / "findings.json").is_file() or (path / "assessment.json").is_file():
            return path
        nested = path / "current"
        if (nested / "findings.json").is_file() or (nested / "assessment.json").is_file():
            return nested
        if path.is_dir() and any(path.rglob("findings.json")):
            matches = sorted(path.rglob("findings.json"))
            return matches[0].parent if matches else path
        return None

    def _resolve_work(provider: str) -> Path | None:
        provider_root = WORK_ASSESS_OUT / provider
        candidates = (
            provider_root / catalog_id,
            provider_root / f"local-{catalog_id}",
            provider_root / catalog_id / "current",
            provider_root / f"local-{catalog_id}" / "current",
        )
        for candidate in candidates:
            found = _if_present(candidate)
            if found is not None:
                return found
        if not provider_root.is_dir():
            return None
        needle = catalog_id.lower()
        for child in sorted(provider_root.iterdir()):
            if not child.is_dir():
                continue
            if needle in child.name.lower():
                found = _if_present(child)
                if found is not None:
                    return found
        return None

    return {
        "github_current": github_current,
        "work_no_ai": _resolve_work("no-ai"),
        "work_bedrock": _resolve_work("bedrock"),
        "work_openai": _resolve_work("openai"),
        "work_openrouter": _resolve_work("openrouter"),
    }


def _rel(monorepo: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(monorepo))
    except ValueError:
        # Outside monorepo (e.g. /tmp/sv17-20-work): keep basename trail only.
        parts = path.parts
        if "sv17-20-work" in parts:
            idx = parts.index("sv17-20-work")
            return "/".join(("tmp",) + parts[idx:])
        return path.name


def select_repositories(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = ["bounded_representative_repositories"]

    catalog = _catalog_by_id(monorepo)
    selected: list[dict[str, Any]] = []

    # Prefer flask + juice-shop; fall back to express for second slot.
    primary = "flask" if "flask" in catalog else None
    secondary = None
    for cand in ("juice-shop", "express"):
        if cand in catalog and cand != primary:
            secondary = cand
            break

    chosen = [c for c in (primary, secondary) if c]
    if len(chosen) < 2:
        # Fill from preferred list
        for cand in REPRESENTATIVE_PREFERRED:
            if cand in catalog and cand not in chosen:
                chosen.append(cand)
            if len(chosen) >= 2:
                break

    checks.append(
        check(
            "repositories:selected_count",
            len(chosen) >= 2,
            f"selected={chosen}",
            "repositories",
        )
    )
    if len(chosen) < 2:
        defects.append(
            hard_defect(
                "insufficient_repositories",
                "repositories:selected_count",
                ">=2",
                str(len(chosen)),
            )
        )

    for catalog_id in chosen:
        item = catalog[catalog_id]
        github_repo = str(item.get("github_repository") or "")
        dirs = resolve_assessment_dirs(
            monorepo, catalog_id, github_repository=github_repo or None
        )
        row = {
            "catalog_id": catalog_id,
            "reason": SELECTION_REASONS.get(catalog_id, "representative"),
            "github_repository": github_repo,
            "artifact_folder": github_artifact_folder(github_repo) if github_repo else None,
            "github_current": _rel(monorepo, dirs["github_current"]),
            "work_no_ai": _rel(monorepo, dirs["work_no_ai"]),
            "work_bedrock": _rel(monorepo, dirs["work_bedrock"]),
            "work_openai": _rel(monorepo, dirs["work_openai"]),
            "work_openrouter": _rel(monorepo, dirs["work_openrouter"]),
            "has_baseline_artifact": bool(
                dirs["work_no_ai"] or dirs["github_current"]
            ),
            "_github_current_path": dirs["github_current"],
            "_work_no_ai_path": dirs["work_no_ai"],
            "_work_bedrock_path": dirs["work_bedrock"],
            "_work_openai_path": dirs["work_openai"],
            "_work_openrouter_path": dirs["work_openrouter"],
        }
        selected.append(row)
        checks.append(
            check(
                f"repositories:{catalog_id}_resolvable",
                row["has_baseline_artifact"],
                f"github={bool(dirs['github_current'])} work_no_ai={bool(dirs['work_no_ai'])}",
                "repositories",
            )
        )

    work_present = WORK_ASSESS_OUT.is_dir()
    checks.append(
        check(
            "repositories:work_root_optional",
            True,
            f"work_assess_out={'present' if work_present else 'absent'}",
            "repositories",
        )
    )

    summary = {
        "selected": selected,
        "work_assess_out_present": work_present,
        "selection_policy": "flask + juice-shop (or express)",
    }
    _ = json  # reserved
    return checks, defects, summary, limitations
