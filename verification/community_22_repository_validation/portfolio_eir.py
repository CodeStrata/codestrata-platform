"""Write ONE portfolio Engineering Intelligence report for Slice 17.13."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.assessment import find_assessment_runs
from verification.community_22_repository_validation.catalog import CatalogRepository
from verification.community_22_repository_validation.contract import INTELLIGENCE_RELATIVE
from verification.community_22_repository_validation.ei_compose import compose_assessment_document


def _portfolio_run_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"portfolio-sv17-13-{stamp}"


def build_portfolio_eir(
    monorepo: Path,
    repositories: tuple[CatalogRepository, ...],
    *,
    repository_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate a single portfolio EIR under ``.codestrata-artifacts/intelligence/``."""

    import sys

    engine = str((monorepo / "engine").resolve())
    platform_root = str((monorepo / "platform").resolve())
    platform_src = str((monorepo / "platform" / "src").resolve())
    for path in (str(monorepo.resolve()), engine, platform_root, platform_src):
        if path not in sys.path:
            sys.path.insert(0, path)

    # Merge Engine + Platform verification namespaces.
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

    from verification.engineering_intelligence.assessment_inputs import PreparedAssessment
    from verification.engineering_intelligence.ingestion import build_pipeline_from_assessments
    from codestrata_platform.intelligence_reporting.application.website_export.builder import (
        build_website_safe_export,
    )
    from codestrata_platform.intelligence_reporting.infrastructure.static_export_writer import (
        StaticIntelligenceExportWriter,
    )

    prepared: list[PreparedAssessment] = []
    coverage: list[dict[str, Any]] = []
    result_by_id = {
        str(r.get("repository_validation_id")): r for r in (repository_results or [])
    }

    for repo in repositories:
        runs = find_assessment_runs(monorepo, repo.repository_id)
        status = (result_by_id.get(repo.repository_id) or {}).get("assessment_status")
        if not runs:
            coverage.append(
                {
                    "repository_validation_id": repo.repository_id,
                    "included": False,
                    "reason": "assessment_missing",
                    "assessment_status": status or "not_executed",
                }
            )
            continue
        if status not in {None, "pass", "present", "pass_with_limitations"}:
            coverage.append(
                {
                    "repository_validation_id": repo.repository_id,
                    "included": False,
                    "reason": f"assessment_status:{status}",
                    "assessment_status": status,
                    "assessment_run_id": runs[0].name,
                }
            )
            continue

        run_dir = runs[0]
        document = compose_assessment_document(run_dir, repo)
        digest_material = json.dumps(document, sort_keys=True, separators=(",", ":"))
        import hashlib

        digest = hashlib.sha256(digest_material.encode("utf-8")).hexdigest()
        prepared.append(
            PreparedAssessment(
                repository_id=repo.repository_id,
                project_name=repo.project_name,
                github_repository=repo.github_repository,
                qualified_revision=repo.qualified_revision_value,
                source_tag=repo.qualified_revision_source_tag,
                language_group=str(repo.language_group or ""),
                assessment_run_reference=f"assessments/{run_dir.name}",
                report_path=run_dir / "assessment.json",
                report_digest=digest,
                schema_version=str(document.get("schema_version") or ""),
                source="sv17-13",
                report_document=document,
            )
        )
        coverage.append(
            {
                "repository_validation_id": repo.repository_id,
                "included": True,
                "assessment_run_id": run_dir.name,
                "assessment_status": status or "pass",
            }
        )

    if not prepared:
        raise RuntimeError("no successful assessments available for portfolio EIR")

    portfolio_id = _portfolio_run_id()
    out = monorepo / INTELLIGENCE_RELATIVE / portfolio_id
    out.mkdir(parents=True, exist_ok=True)

    pipeline = build_pipeline_from_assessments(
        prepared,
        title="CodeStrata SV.17.13 Portfolio Engineering Intelligence (22 curated repositories)",
    )
    export = build_website_safe_export(pipeline.report)
    StaticIntelligenceExportWriter().write(export, out, overwrite=True)

    # Ensure expected filenames exist (writer may use report names already).
    json_path = out / "engineering-intelligence-report.json"
    html_path = out / "engineering-intelligence-report.html"
    if not json_path.is_file():
        json_path.write_text(
            json.dumps(pipeline.report_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    coverage_path = out / "coverage.json"
    coverage_path.write_text(
        json.dumps(
            {
                "portfolio_run_id": portfolio_id,
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

    return {
        "portfolio_run_id": portfolio_id,
        "output_relative": f"{INTELLIGENCE_RELATIVE}/{portfolio_id}",
        "included": sum(1 for c in coverage if c.get("included")),
        "excluded": sum(1 for c in coverage if not c.get("included")),
        "json_present": json_path.is_file(),
        "html_present": html_path.is_file() or any(out.glob("*.html")),
        "coverage": coverage,
    }
