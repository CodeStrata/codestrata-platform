"""Generate portfolio Engineering Intelligence report for Slice 17.19."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import (
    EIR_HTML,
    EIR_JSON,
    INTELLIGENCE_RELATIVE,
    PORTFOLIO_ID,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    load_json,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def _extend_sys_path(monorepo: Path) -> None:
    engine = str((monorepo / "engine").resolve())
    platform_root = str((monorepo / "platform").resolve())
    platform_src = str((monorepo / "platform" / "src").resolve())
    for path in (str(monorepo.resolve()), engine, platform_root, platform_src):
        if path not in sys.path:
            sys.path.insert(0, path)

    import verification as verification_pkg
    from pkgutil import extend_path

    verification_pkg.__path__ = extend_path(
        list(verification_pkg.__path__), verification_pkg.__name__
    )
    platform_verification = monorepo / "platform" / "verification"
    if platform_verification.is_dir():
        path = str(platform_verification.resolve())
        if path not in verification_pkg.__path__:
            verification_pkg.__path__.append(path)


def _load_catalog_repos(monorepo: Path, catalog_ids: list[str]) -> list[Any]:
    from verification.community_22_repository_validation.catalog import CatalogRepository

    catalog = load_json(monorepo / "validation/repository-catalog/catalog.json")
    by_id = {
        str(item["id"]): item
        for item in (catalog.get("repositories") or [])
        if isinstance(item, dict) and item.get("id")
    }
    repos: list[Any] = []
    for catalog_id in catalog_ids:
        item = by_id[catalog_id]
        rev = item.get("qualified_revision") or {}
        repos.append(
            CatalogRepository(
                repository_id=str(item["id"]),
                project_name=str(item.get("project_name") or item["id"]),
                github_repository=str(item.get("github_repository") or ""),
                github_url=str(item.get("github_url") or ""),
                language_group=item.get("language_group"),
                ecosystem=item.get("dependency_ecosystem"),
                qualified_revision_type=str(rev.get("type") or "commit"),
                qualified_revision_value=str(rev.get("value") or "").lower(),
                qualified_revision_source_tag=(
                    str(rev["source_tag"]).strip()
                    if isinstance(rev.get("source_tag"), str) and rev.get("source_tag")
                    else None
                ),
                requires_submodules=bool(item.get("requires_submodules")),
                requires_git_lfs=bool(item.get("requires_git_lfs")),
                enabled_for={k: bool(v) for k, v in (item.get("enabled_for") or {}).items()},
                raw=item,
            )
        )
    return repos


def generate_eir_for_selection(
    monorepo: Path,
    selection: dict[str, Any],
    *,
    catalog_ids: list[str] | None = None,
    portfolio_id: str = PORTFOLIO_ID,
) -> dict[str, Any]:
    """Build and promote an EIR for the representative assessments."""

    _extend_sys_path(monorepo)

    from verification.community_22_repository_validation.ei_compose import (
        compose_assessment_document,
    )
    from verification.engineering_intelligence.assessment_inputs import PreparedAssessment
    from verification.engineering_intelligence.ingestion import build_pipeline_from_assessments
    from codestrata_platform.intelligence_reporting.application.website_export.builder import (
        build_website_safe_export,
    )
    from codestrata_platform.intelligence_reporting.infrastructure.static_export_writer import (
        StaticIntelligenceExportWriter,
    )
    from codestrata.artifacts.lifecycle import (
        promote_intelligence_run,
        staging_intelligence_directory,
    )

    selected = selection.get("selected") or []
    ids = catalog_ids or [str(s["catalog_id"]) for s in selected if s.get("current_relative")]
    repos = _load_catalog_repos(monorepo, ids)
    by_id = {str(s["catalog_id"]): s for s in selected}

    prepared: list[Any] = []
    coverage: list[dict[str, Any]] = []
    for repo in repos:
        meta = by_id.get(repo.repository_id) or {}
        rel = meta.get("current_relative")
        if not rel:
            coverage.append(
                {
                    "catalog_id": repo.repository_id,
                    "included": False,
                    "reason": "assessment_missing",
                }
            )
            continue
        run_dir = monorepo / str(rel)
        document = compose_assessment_document(run_dir, repo)
        digest = hashlib.sha256(
            json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        prepared.append(
            PreparedAssessment(
                repository_id=repo.repository_id,
                project_name=repo.project_name,
                github_repository=repo.github_repository,
                qualified_revision=repo.qualified_revision_value,
                source_tag=repo.qualified_revision_source_tag,
                language_group=str(repo.language_group or ""),
                assessment_run_reference=f"assessments/{run_dir.parent.name}/current",
                report_path=run_dir / "assessment.json",
                report_digest=digest,
                schema_version=str(document.get("schema_version") or ""),
                source="sv17-19",
                report_document=document,
            )
        )
        coverage.append(
            {
                "catalog_id": repo.repository_id,
                "included": True,
                "assessment_run_id": str(
                    (load_json(run_dir / "assessment.json")).get("assessment_run_id") or ""
                ),
                "artifact_folder": run_dir.parent.name,
            }
        )

    if len(prepared) < 2:
        raise RuntimeError(f"need >=2 assessments for EIR, got {len(prepared)}")

    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    run_id = f"portfolio-{portfolio_id}-{stamp}"
    staging = staging_intelligence_directory(run_id, base=monorepo)

    pipeline = build_pipeline_from_assessments(
        prepared,
        title=f"CodeStrata SV.17.19 Portfolio Engineering Intelligence ({portfolio_id})",
    )
    export = build_website_safe_export(pipeline.report)
    StaticIntelligenceExportWriter().write(export, staging, overwrite=True)

    json_path = staging / EIR_JSON
    html_path = staging / EIR_HTML
    if not json_path.is_file():
        json_path.write_text(
            json.dumps(pipeline.report_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    # Annotate portfolio identity for validation.
    if json_path.is_file():
        payload = load_json(json_path)
        payload["portfolio_id"] = portfolio_id
        payload["portfolio_run_id"] = run_id
        payload.setdefault("dataset_summary", {})
        if isinstance(payload["dataset_summary"], dict):
            payload["dataset_summary"]["repository_count"] = len(prepared)
        json_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    coverage_path = staging / "coverage.json"
    coverage_path.write_text(
        json.dumps(
            {
                "portfolio_id": portfolio_id,
                "portfolio_run_id": run_id,
                "included_count": sum(1 for c in coverage if c.get("included")),
                "excluded_count": sum(1 for c in coverage if not c.get("included")),
                "repositories": coverage,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    current = promote_intelligence_run(
        portfolio_id=portfolio_id,
        staging_directory=staging,
        base=monorepo,
    )
    report_json = current / EIR_JSON
    section_keys: list[str] = []
    repository_count = len(prepared)
    if report_json.is_file():
        payload = load_json(report_json)
        section_keys = sorted(payload.keys())
        ds = payload.get("dataset_summary") if isinstance(payload.get("dataset_summary"), dict) else {}
        repository_count = int(ds.get("repository_count") or repository_count)

    return {
        "generated": True,
        "portfolio_id": portfolio_id,
        "portfolio_run_id": run_id,
        "output_relative": f"{INTELLIGENCE_RELATIVE}/{portfolio_id}/current",
        "included": sum(1 for c in coverage if c.get("included")),
        "repository_count": repository_count,
        "json_present": (current / EIR_JSON).is_file(),
        "html_present": (current / EIR_HTML).is_file(),
        "section_inventory": section_keys,
        "coverage": coverage,
        "rescanned": False,
    }


def check_eir_generation(
    monorepo: Path,
    selection: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    summary: dict[str, Any] = {"generated": False}

    try:
        summary = generate_eir_for_selection(monorepo, selection)
    except Exception as exc:  # noqa: BLE001
        checks.append(
            check(
                "eir_generation:built",
                False,
                type(exc).__name__,
                "eir_generation",
            )
        )
        defects.append(
            hard_defect(
                "eir_generation_failed",
                "eir_generation:built",
                "generated",
                type(exc).__name__,
            )
        )
        return checks, defects, summary, limitations

    ok = (
        summary.get("generated") is True
        and int(summary.get("repository_count") or 0) >= 2
        and summary.get("json_present")
        and summary.get("html_present")
    )
    checks.append(
        check(
            "eir_generation:built",
            ok,
            f"repos={summary.get('repository_count')};json={summary.get('json_present')}",
            "eir_generation",
        )
    )
    if not ok:
        defects.append(
            hard_defect(
                "eir_incomplete",
                "eir_generation:built",
                ">=2 repos + json/html",
                str(summary.get("repository_count")),
            )
        )

    checks.append(
        check(
            "eir_generation:no_rescan",
            summary.get("rescanned") is False,
            "consumes assessment artifacts only",
            "eir_generation",
        )
    )
    checks.append(
        check(
            "eir_generation:section_inventory",
            bool(summary.get("section_inventory")),
            f"keys={len(summary.get('section_inventory') or [])}",
            "eir_generation",
        )
    )

    if int(summary.get("repository_count") or 0) < 6:
        limitations.append("low_portfolio_size")
    limitations.append("bounded_representative_subset")
    limitations.append("ai_narrative_not_requested")

    return checks, defects, summary, limitations
