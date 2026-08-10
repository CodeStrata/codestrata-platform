"""Compose Engineering Intelligence assessment inputs from Slice 17.12 artifacts.

``assessment.json`` is a lightweight manifest. Portfolio EI still requires a
schema 1.2 assessment document. This composer builds an EI-only in-memory
document from ``findings.json``, ``recommendations.json``, heads, and the
manifest — without writing a giant collapsed Community assessment.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from codestrata_platform.intelligence_reporting.application.contracts import (
    SUPPORTED_ASSESSMENT_SCHEMA_VERSION,
)

from verification.community_22_repository_validation.catalog import CatalogRepository


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def compose_assessment_document(run_dir: Path, repo: CatalogRepository) -> dict[str, Any]:
    """Build a portfolio-EI input document from a completed assessment run."""

    manifest_path = run_dir / "assessment.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing assessment.json under {run_dir.name}")
    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("assessment.json must be an object")

    findings_doc: dict[str, Any] = {}
    findings_path = run_dir / "findings.json"
    if findings_path.is_file():
        raw = _load_json(findings_path)
        if isinstance(raw, dict):
            findings_doc = raw
        elif isinstance(raw, list):
            findings_doc = {"findings": raw}

    recommendations_doc: dict[str, Any] = {}
    recommendations_path = run_dir / "recommendations.json"
    if recommendations_path.is_file():
        raw = _load_json(recommendations_path)
        if isinstance(raw, dict):
            recommendations_doc = raw
        elif isinstance(raw, list):
            recommendations_doc = {"recommendations": raw}

    heads: dict[str, Any] = {}
    heads_dir = run_dir / "heads"
    if heads_dir.is_dir():
        for path in sorted(heads_dir.glob("*.json")):
            try:
                heads[path.stem] = _load_json(path)
            except json.JSONDecodeError as exc:
                raise ValueError(f"corrupt head {path.name}") from exc

    findings = findings_doc.get("findings")
    if findings is None and isinstance(findings_doc.get("items"), list):
        findings = findings_doc["items"]
    if not isinstance(findings, list):
        findings = []

    recommendations = (
        recommendations_doc.get("recommendations")
        or recommendations_doc.get("deterministic_recommendations")
        or recommendations_doc.get("items")
        or []
    )
    if not isinstance(recommendations, list):
        recommendations = []

    # EI aggregation requires finding.primary_evidence_id to resolve against
    # assessment.evidence[]. Synthesize minimal evidence rows from refs.
    evidence_ids: set[str] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        primary = finding.get("primary_evidence_id")
        if isinstance(primary, str) and primary.strip():
            evidence_ids.add(primary.strip())
        for ref in finding.get("evidence_refs") or []:
            if isinstance(ref, dict):
                eid = ref.get("evidence_id") or ref.get("id")
                if isinstance(eid, str) and eid.strip():
                    evidence_ids.add(eid.strip())
        for eid in finding.get("synthesized_from_evidence_ids") or []:
            if isinstance(eid, str) and eid.strip():
                evidence_ids.add(eid.strip())
    evidence = [
        {
            "evidence_id": eid,
            "id": eid,
            "evidence_type": "assessment_artifact_reference",
            "source": "sv17-13_ei_compose",
        }
        for eid in sorted(evidence_ids)
    ]

    git = manifest.get("git") if isinstance(manifest.get("git"), dict) else {}
    document: dict[str, Any] = {
        "schema_version": SUPPORTED_ASSESSMENT_SCHEMA_VERSION,
        "repository": {
            "name": str(manifest.get("repository") or repo.project_name),
            "commit": git.get("commit") or repo.qualified_revision_value,
            "branch": git.get("branch"),
            "remote": git.get("remote") or f"https://github.com/{repo.github_repository}",
        },
        "assessment": {
            "id": str(manifest.get("assessment_id") or run_dir.name),
            "summary": manifest.get("summary"),
            "scores": manifest.get("scores") or {},
            "findings_summary": manifest.get("findings_summary") or {},
            "findings": findings,
            "evidence": evidence,
            "deterministic_recommendations": recommendations,
            "assessment_heads": heads,
            "completed_heads": manifest.get("completed_heads") or [],
            "engine_version": manifest.get("engine_version"),
            "execution_status": manifest.get("execution_status"),
        },
        "provenance": {
            "source": "sv17-13_artifact_composer",
            "assessment_run_id": run_dir.name,
            "repository_validation_id": repo.repository_id,
            "artifact_layout": "codestrata-artifacts-v1",
        },
    }
    return document
