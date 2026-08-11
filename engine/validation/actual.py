"""Load the shipped 0.2.0 assessment artifact contract into ActualAssessmentResult.

ACTIVE_0_2_0_RELEASE_GATE: on-disk ``assessment.json`` is the lightweight
manifest. Companion evidence is ``findings.json``, ``recommendations.json``,
``heads/*.json``, and ``graphs/repository-manifest.json``. This harness merges
those persisted sidecars only — it does not synthesize priority_actions,
roadmap, schema_version 1.2, or categorized technology inventory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from codestrata.application.assessment import run_assessment
from codestrata.reporting.contract.canonical import strip_volatile_fields
from codestrata.reporting.modernization_models import AssessmentMode
from validation.compare import normalize_repo_relative_path
from validation.models import ActualAssessmentResult
from validation.security import extract_security_findings
from validation.architecture import extract_architecture_findings, extract_architecture_graph
from validation.technical_debt import extract_technical_debt_findings
from validation.dependency import (
    discover_dependency_artifact_paths,
    extract_dependency_findings,
    extract_dependency_manifests,
)
from validation.cloud import (
    discover_cloud_artifact_paths,
    extract_cloud_findings,
    extract_cloud_recommendations,
    extract_cloud_signals,
)
from validation.ai_readiness import (
    discover_ai_readiness_artifact_paths,
    extract_ai_readiness_findings,
    extract_ai_readiness_recommendations,
    extract_ai_readiness_signals,
)
from validation.finding_correlations.expectations import extract_correlation_pair_keys
from validation.modernization import (
    build_modernization_finding_index,
    extract_modernization_priority_actions,
    extract_modernization_recommendations,
    extract_modernization_roadmap_initiatives,
)


_HEAD_ID_TO_ASSESSMENT_KEY = {
    "architecture": "architecture",
    "security": "security",
    "technical-debt": "technical_debt",
    "cloud": "cloud",
    "ai": "ai_readiness",
    "dependencies": "dependency",
    "testing": "testing",
    "performance": "performance",
}


def load_report_document(report_path: Path) -> dict[str, Any]:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"assessment JSON must be an object: {report_path}")
    return payload


def _load_json_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def persisted_layout_for_document(document: dict[str, Any]) -> str:
    schema = str(document.get("schema") or "")
    if schema.startswith("codestrata-assessment-manifest"):
        return "manifest_0_2_0"
    return "full_report_json"


def merge_persisted_sidecars(
    document: dict[str, Any],
    report_path: Path,
) -> dict[str, Any]:
    """Attach companion artifacts that 0.2.0 actually writes next to the manifest.

    Does **not** synthesize priority_actions, roadmap, schema_version 1.2, or
    categorized technology inventory — those are not persisted in assessment.json.
    """

    if persisted_layout_for_document(document) != "manifest_0_2_0":
        return document

    from codestrata.artifacts.heads import ASSESSMENT_HEAD_SPECS

    parent = report_path.parent
    findings_doc = _load_json_object(parent / "findings.json") or {}
    recs_doc = _load_json_object(parent / "recommendations.json") or {}
    findings = findings_doc.get("findings") if isinstance(findings_doc.get("findings"), list) else []
    recommendations = (
        recs_doc.get("recommendations")
        if isinstance(recs_doc.get("recommendations"), list)
        else []
    )

    technologies: list[dict[str, str]] = []
    seen: set[str] = set()
    repo_manifest = _load_json_object(parent / "graphs" / "repository-manifest.json") or {}
    for row in repo_manifest.get("files") or []:
        if not isinstance(row, dict):
            continue
        language = row.get("language")
        if isinstance(language, str) and language.strip() and language not in seen:
            seen.add(language)
            technologies.append({"name": language, "category": "language"})

    status = document.get("execution_status") or "completed"
    assessment: dict[str, Any] = {
        "status": status,
        "summary": {
            "finding_count": findings_doc.get("finding_count", len(findings)),
            "recommendation_count": recs_doc.get("recommendation_count", len(recommendations)),
            "ai_executed": False,
            "status": status,
        },
        "findings": findings,
        "recommendations": recommendations,
        "technologies": technologies,
        "ai": {"executed": False},
    }
    for spec in ASSESSMENT_HEAD_SPECS:
        head_doc = _load_json_object(parent / "heads" / spec.heads_basename)
        if head_doc is None:
            continue
        key = _HEAD_ID_TO_ASSESSMENT_KEY.get(spec.head_id, spec.head_id.replace("-", "_"))
        assessment[key] = head_doc

    merged = {
        **document,
        "status": status,
        "findings": findings,
        "recommendations": recommendations,
        "technologies": technologies,
        "assessment": assessment,
    }
    return merged


def locate_persisted_assessment(artifact_dir: str | Path) -> Path:
    """Return shipped ``assessment.json``, or legacy ``report.json`` if present."""

    root = Path(artifact_dir)
    current = sorted(path for path in root.rglob("assessment.json") if path.is_file())
    if current:
        return current[0]
    legacy = sorted(path for path in root.rglob("report.json") if path.is_file())
    if legacy:
        return legacy[0]
    raise FileNotFoundError(f"no assessment.json under {artifact_dir}")


def load_emitted_assessment(artifact_dir: str | Path) -> tuple[Path, dict[str, Any]]:
    """Load persisted 0.2.0 assessment.json and merge companion sidecars."""

    path = locate_persisted_assessment(artifact_dir)
    document = merge_persisted_sidecars(load_report_document(path), path)
    return path, document


def actual_from_report(
    document: dict[str, Any],
    *,
    artifact_paths: dict[str, str] | None = None,
    assessment_duration_ms: float | None = None,
    ai_executed: bool = False,
) -> ActualAssessmentResult:
    """Normalize report.json into comparison-ready actual results."""

    assessment = document.get("assessment") if isinstance(document.get("assessment"), dict) else {}
    summary = assessment.get("summary") if isinstance(assessment.get("summary"), dict) else {}

    technologies = _technology_names(assessment.get("technologies") or document.get("technologies"))
    findings = assessment.get("findings") or document.get("findings") or []
    recommendations = assessment.get("recommendations") or document.get("recommendations") or []
    priority_actions = (
        assessment.get("priority_actions") or document.get("priority_actions") or []
    )
    roadmap = assessment.get("roadmap") if isinstance(assessment.get("roadmap"), dict) else {}
    phases = roadmap.get("phases") or []

    finding_rule_ids = tuple(
        sorted(
            {
                str(item.get("rule_id") or item.get("id") or "")
                for item in findings
                if isinstance(item, dict) and (item.get("rule_id") or item.get("id"))
            }
        )
    )
    finding_ids = tuple(
        sorted(
            {
                str(item.get("id") or "")
                for item in findings
                if isinstance(item, dict) and item.get("id")
            }
        )
    )
    recommendation_ids = tuple(
        sorted(
            {
                str(item.get("id") or item.get("recommendation_id") or "")
                for item in recommendations
                if isinstance(item, dict)
                and (item.get("id") or item.get("recommendation_id"))
            }
        )
    )
    recommendation_categories = tuple(
        sorted(
            {
                str(item.get("category") or item.get("dimension") or "")
                for item in recommendations
                if isinstance(item, dict) and (item.get("category") or item.get("dimension"))
            }
        )
    )
    priority_categories = tuple(
        sorted(
            {
                str(item.get("category") or item.get("dimension") or item.get("area") or "")
                for item in priority_actions
                if isinstance(item, dict)
                and (item.get("category") or item.get("dimension") or item.get("area"))
            }
        )
    )
    roadmap_phases = tuple(
        sorted(
            {
                str(item.get("id") or item.get("name") or item.get("phase") or "")
                for item in phases
                if isinstance(item, dict)
                and (item.get("id") or item.get("name") or item.get("phase"))
            }
        )
    )

    coverage_states = _collect_string_values(
        assessment.get("coverage"),
        keys=("state", "status", "coverage_state"),
    )
    confidence = _collect_string_values(
        assessment.get("confidence"),
        keys=("level", "status", "confidence"),
    )
    limitations = _limitations(assessment)
    evidence_paths = _evidence_paths(findings, recommendations, assessment)
    repository_facts = _repository_facts(assessment)

    status = (
        summary.get("status")
        or assessment.get("status")
        or document.get("status")
    )
    schema_version = document.get("schema_version")
    findings_count = int(summary.get("finding_count") or len(findings) or 0)
    recommendations_count = int(
        summary.get("recommendation_count") or len(recommendations) or 0
    )
    warnings = tuple(
        str(item)
        for item in (assessment.get("warnings") or document.get("warnings") or [])
        if item
    )
    assessment_heads = _assessment_heads(assessment)
    ai_block = assessment.get("ai") if isinstance(assessment.get("ai"), dict) else {}
    report_ai_executed = bool(
        ai_block.get("executed")
        if ai_block.get("executed") is not None
        else summary.get("ai_executed")
    )
    effective_ai = bool(ai_executed or report_ai_executed)

    tech_rows = assessment.get("technologies") or document.get("technologies") or []
    by_category, versions = _technologies_categorized(tech_rows)
    ecosystems = _dependency_ecosystems(assessment, by_category)
    indicators = _application_indicators(assessment, summary)
    composition = _composition_facts(assessment)
    security_findings = extract_security_findings(
        findings if isinstance(findings, list) else []
    )
    architecture_findings = extract_architecture_findings(
        findings if isinstance(findings, list) else []
    )
    architecture_graph = extract_architecture_graph(document)
    technical_debt_findings = extract_technical_debt_findings(
        findings if isinstance(findings, list) else []
    )
    dependency_findings = extract_dependency_findings(
        findings if isinstance(findings, list) else []
    )
    dependency_manifests = extract_dependency_manifests(
        document,
        artifact_paths=artifact_paths,
    )
    cloud_findings = extract_cloud_findings(
        findings if isinstance(findings, list) else []
    )
    cloud_signals = extract_cloud_signals(
        document,
        artifact_paths=artifact_paths,
    )
    cloud_recommendations = extract_cloud_recommendations(document)
    ai_readiness_findings = extract_ai_readiness_findings(
        findings if isinstance(findings, list) else []
    )
    ai_readiness_signals = extract_ai_readiness_signals(
        document,
        artifact_paths=artifact_paths,
    )
    ai_readiness_recommendations = extract_ai_readiness_recommendations(document)
    modernization_finding_index = build_modernization_finding_index(document)
    modernization_recommendations = extract_modernization_recommendations(
        document,
        finding_index=modernization_finding_index,
    )
    modernization_priority_actions = extract_modernization_priority_actions(document)
    modernization_roadmap_initiatives = extract_modernization_roadmap_initiatives(
        document
    )
    correlations_raw = (
        assessment.get("finding_correlations")
        or document.get("finding_correlations")
        or []
    )
    finding_correlation_pairs = extract_correlation_pair_keys(
        findings=list(findings) if isinstance(findings, list) else [],
        correlations=list(correlations_raw) if isinstance(correlations_raw, list) else [],
    )

    return ActualAssessmentResult(
        schema_version=str(schema_version) if schema_version is not None else None,
        assessment_status=str(status) if status is not None else None,
        technologies=technologies,
        repository_facts=repository_facts,
        evidence_paths=evidence_paths,
        finding_rule_ids=finding_rule_ids,
        finding_ids=finding_ids,
        findings_count=findings_count,
        recommendation_ids=recommendation_ids,
        recommendation_categories=recommendation_categories,
        recommendations_count=recommendations_count,
        priority_action_categories=priority_categories,
        roadmap_phases=roadmap_phases,
        coverage_states=coverage_states,
        confidence=confidence,
        limitations=limitations,
        execution_warnings=warnings,
        assessment_heads=assessment_heads,
        technologies_by_category=by_category,
        technology_versions=versions,
        dependency_ecosystems=ecosystems,
        application_indicators=indicators,
        repository_composition_facts=composition,
        security_findings=security_findings,
        architecture_findings=architecture_findings,
        architecture_graph=architecture_graph,
        technical_debt_findings=technical_debt_findings,
        dependency_findings=dependency_findings,
        dependency_manifests=dependency_manifests,
        cloud_findings=cloud_findings,
        cloud_signals=cloud_signals,
        cloud_recommendations=cloud_recommendations,
        ai_readiness_findings=ai_readiness_findings,
        ai_readiness_signals=ai_readiness_signals,
        ai_readiness_recommendations=ai_readiness_recommendations,
        modernization_recommendations=modernization_recommendations,
        modernization_priority_actions=modernization_priority_actions,
        modernization_roadmap_initiatives=modernization_roadmap_initiatives,
        finding_correlation_pairs=finding_correlation_pairs,
        artifact_paths=dict(artifact_paths or {}),
        assessment_duration_ms=assessment_duration_ms,
        ai_executed=effective_ai,
        report_document=strip_volatile_fields(document),
        persisted_layout=persisted_layout_for_document(document),
    )


def run_real_assessment(
    *,
    repository_path: Path,
    output_directory: Path,
    config_path: Path | None = None,
) -> tuple[ActualAssessmentResult, Path]:
    """Invoke the real customer assessment path with AI disabled.

    Uses ``AssessmentMode.DETERMINISTIC`` (equivalent to ``codestrata assess --no-ai``).
    """

    from codestrata.config import load_settings

    output_directory.mkdir(parents=True, exist_ok=True)
    kwargs: dict[str, Any] = {
        "repo": str(repository_path),
        "output_directory": output_directory,
        "mode": AssessmentMode.DETERMINISTIC,
        "quiet": True,
        "static_analysis_enabled": False,
    }
    if config_path is not None:
        # Validation overlays may omit repository.path/url; the harness supplies
        # the concrete repo via ``repo=``. Skip profile "repository required"
        # checks and stamp the assessed path onto settings.
        loaded = load_settings(config_path, validate_profile=False)
        loaded = loaded.model_copy(
            update={
                "repository": loaded.repository.model_copy(
                    update={"path": str(repository_path.resolve())}
                )
            }
        )
        kwargs["settings"] = loaded
        kwargs["config_path"] = config_path

    result = run_assessment(**kwargs)
    if result.ai_executed:
        raise RuntimeError(
            "validation harness requires AI disabled; assessment reported ai_executed"
        )

    report_path = Path(result.json_report_path)
    if not report_path.is_file():
        raise FileNotFoundError(f"assessment.json not produced at {report_path}")

    document = merge_persisted_sidecars(load_report_document(report_path), report_path)
    artifact_paths = {
        "assessment.json": str(report_path),
        "assessment.html": str(result.html_report_path),
        "html": str(result.html_report_path),
    }
    if result.findings_artifact_path:
        artifact_paths["findings.json"] = str(result.findings_artifact_path)
    if result.recommendations_artifact_path:
        artifact_paths["recommendations.json"] = str(result.recommendations_artifact_path)
    artifact_paths.update(discover_dependency_artifact_paths(report_path))
    artifact_paths.update(discover_cloud_artifact_paths(report_path))
    artifact_paths.update(discover_ai_readiness_artifact_paths(report_path))

    actual = actual_from_report(
        document,
        artifact_paths=artifact_paths,
        assessment_duration_ms=result.duration_ms,
        ai_executed=bool(result.ai_executed),
    )
    return actual, report_path


def normalized_for_determinism(actual: ActualAssessmentResult) -> dict[str, Any]:
    """Stable payload for repeat-run comparison (volatile fields excluded).

    Explicitly excludes:
    - assessment_duration_ms
    - absolute artifact_paths
    - full report_document (may embed run directories / timestamps)

    Canonical IDs, findings, recommendations, Priority Actions, roadmap
    membership, evidence references, status, coverage, and limitations remain.
    """

    return {
        "schema_version": actual.schema_version,
        "assessment_status": actual.assessment_status,
        "technologies": list(actual.technologies),
        "repository_facts": list(actual.repository_facts),
        "evidence_paths": list(actual.evidence_paths),
        "finding_rule_ids": list(actual.finding_rule_ids),
        "finding_ids": list(actual.finding_ids),
        "findings_count": actual.findings_count,
        "recommendation_ids": list(actual.recommendation_ids),
        "recommendation_categories": list(actual.recommendation_categories),
        "recommendations_count": actual.recommendations_count,
        "priority_action_categories": list(actual.priority_action_categories),
        "roadmap_phases": list(actual.roadmap_phases),
        "coverage_states": list(actual.coverage_states),
        "confidence": list(actual.confidence),
        "limitations": list(actual.limitations),
        "execution_warnings": list(actual.execution_warnings),
        "assessment_heads": list(actual.assessment_heads),
        "technologies_by_category": {
            key: list(value) for key, value in sorted(actual.technologies_by_category.items())
        },
        "technology_versions": dict(sorted(actual.technology_versions.items())),
        "dependency_ecosystems": list(actual.dependency_ecosystems),
        "application_indicators": list(actual.application_indicators),
        "repository_composition_facts": list(actual.repository_composition_facts),
        "ai_executed": actual.ai_executed,
    }


def _technology_names(raw: Any) -> tuple[str, ...]:
    names: set[str] = set()
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str) and item.strip():
                names.add(item.strip())
            elif isinstance(item, dict):
                name = item.get("name") or item.get("technology") or item.get("id")
                if name:
                    names.add(str(name))
    elif isinstance(raw, dict):
        for key, value in raw.items():
            if isinstance(value, dict):
                name = value.get("name") or key
                names.add(str(name))
            elif isinstance(value, list):
                names.update(_technology_names(value))
            elif value:
                names.add(str(key))
    return tuple(sorted(names))


def _limitation_text(item: dict[str, Any]) -> str | None:
    text = (
        item.get("summary")
        or item.get("text")
        or item.get("message")
        or item.get("id")
    )
    if text is None:
        return None
    cleaned = str(text).strip()
    return cleaned or None


def _limitations(assessment: dict[str, Any]) -> tuple[str, ...]:
    collected: set[str] = set()
    for key in ("limitations", "assessment_limitations"):
        raw = assessment.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str) and item.strip():
                    collected.add(item.strip())
                elif isinstance(item, dict):
                    text = _limitation_text(item)
                    if text:
                        collected.add(text)
    for section_name in (
        "architecture",
        "technical_debt",
        "dependency",
        "security",
        "cloud",
        "ai_readiness",
        "roadmap",
    ):
        section = assessment.get(section_name)
        if isinstance(section, dict):
            for item in section.get("limitations") or []:
                if isinstance(item, str) and item.strip():
                    collected.add(item.strip())
                elif isinstance(item, dict):
                    text = _limitation_text(item)
                    if text:
                        collected.add(text)
    return tuple(sorted(collected))


def _evidence_paths(
    findings: Any,
    recommendations: Any,
    assessment: dict[str, Any],
) -> tuple[str, ...]:
    paths: set[str] = set()

    def _consume(items: Any) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            for key in ("file", "path", "evidence_path", "location"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    paths.add(normalize_repo_relative_path(value))
            evidence = item.get("evidence")
            if isinstance(evidence, list):
                for entry in evidence:
                    if isinstance(entry, str) and entry.strip():
                        paths.add(normalize_repo_relative_path(entry))
                    elif isinstance(entry, dict):
                        for key in ("file", "path", "location"):
                            value = entry.get(key)
                            if isinstance(value, str) and value.strip():
                                paths.add(normalize_repo_relative_path(value))

    _consume(findings)
    _consume(recommendations)
    _consume(assessment.get("evidence"))
    return tuple(sorted(p for p in paths if p))


def _repository_facts(assessment: dict[str, Any]) -> tuple[str, ...]:
    facts: set[str] = set()
    repo = assessment.get("repository")
    if isinstance(repo, dict):
        for key in ("name", "language", "primary_language", "default_branch"):
            value = repo.get(key)
            if value:
                facts.add(f"{key}={value}")
    return tuple(sorted(facts))


def _collect_string_values(raw: Any, *, keys: tuple[str, ...]) -> tuple[str, ...]:
    values: set[str] = set()
    if isinstance(raw, str) and raw.strip():
        values.add(raw.strip())
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, str) and item.strip():
                values.add(item.strip())
            elif isinstance(item, dict):
                for key in keys:
                    value = item.get(key)
                    if value:
                        values.add(str(value))
    elif isinstance(raw, dict):
        for key in keys:
            value = raw.get(key)
            if value:
                values.add(str(value))
        for key, value in raw.items():
            if isinstance(value, str) and value.strip():
                values.add(f"{key}={value}")
    return tuple(sorted(values))


_ASSESSMENT_HEAD_CANDIDATES = (
    "executive_summary",
    "technologies",
    "findings",
    "recommendations",
    "priority_actions",
    "architecture",
    "technical_debt",
    "dependency",
    "security",
    "testing",
    "cloud",
    "ai_readiness",
    "roadmap",
)


def _assessment_heads(assessment: dict[str, Any]) -> tuple[str, ...]:
    heads: list[str] = []
    for name in _ASSESSMENT_HEAD_CANDIDATES:
        if name in assessment and assessment[name] is not None:
            heads.append(name)
    # Deterministic recommendations may appear under a dedicated key.
    if "deterministic_recommendations" in assessment:
        if "recommendations" not in heads:
            heads.append("recommendations")
    return tuple(heads)


_CATEGORY_BUCKETS: dict[str, str] = {
    "language": "languages",
    "framework": "frameworks",
    "build_tool": "build_systems",
    "runtime": "runtimes",
    "container": "runtimes",
    "library": "libraries",
    "testing": "testing",
    "database": "application_indicators",
    "cloud": "application_indicators",
    "infrastructure": "application_indicators",
    "other": "application_indicators",
}

_ECOSYSTEM_FROM_BUILD: dict[str, str] = {
    "npm": "npm",
    "yarn": "npm",
    "pnpm": "npm",
    "pip": "pip",
    "poetry": "pip",
    "pipenv": "pip",
    "uv": "pip",
    "maven": "maven",
    "gradle": "gradle",
    "composer": "composer",
    "nuget": "nuget",
}


def _technologies_categorized(
    raw: Any,
) -> tuple[dict[str, tuple[str, ...]], dict[str, str | None]]:
    buckets: dict[str, set[str]] = {
        "languages": set(),
        "frameworks": set(),
        "build_systems": set(),
        "runtimes": set(),
        "libraries": set(),
        "testing": set(),
        "application_indicators": set(),
    }
    versions: dict[str, str | None] = {}
    if not isinstance(raw, list):
        return {key: () for key in buckets}, versions
    for item in raw:
        if isinstance(item, str) and item.strip():
            buckets["languages"].add(item.strip())
            continue
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("technology") or item.get("id")
        if not name:
            continue
        name_s = str(name)
        category = str(item.get("category") or "other").strip().lower()
        bucket = _CATEGORY_BUCKETS.get(category, "application_indicators")
        buckets[bucket].add(name_s)
        version = item.get("version")
        versions[name_s] = str(version) if version is not None else None
    return {key: tuple(sorted(value)) for key, value in buckets.items()}, versions


def _dependency_ecosystems(
    assessment: dict[str, Any],
    by_category: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    found: set[str] = set()
    facts = assessment.get("repository_facts")
    if isinstance(facts, dict):
        deps = facts.get("dependencies")
        if isinstance(deps, dict):
            manifests = deps.get("manifests") or []
            if isinstance(manifests, list):
                for manifest in manifests:
                    if isinstance(manifest, dict) and manifest.get("ecosystem"):
                        found.add(str(manifest["ecosystem"]).strip().lower())
            ecosystem = deps.get("ecosystem")
            if ecosystem:
                found.add(str(ecosystem).strip().lower())
    for build_name in by_category.get("build_systems", ()):
        mapped = _ECOSYSTEM_FROM_BUILD.get(build_name.strip().lower())
        if mapped:
            found.add(mapped)
    return tuple(sorted(found))


def _application_indicators(
    assessment: dict[str, Any],
    summary: dict[str, Any],
) -> tuple[str, ...]:
    indicators: set[str] = set()
    caps = summary.get("cloud_capabilities")
    if isinstance(caps, list):
        for item in caps:
            if item:
                indicators.add(str(item).strip().lower())
    elif isinstance(caps, dict):
        for key, value in caps.items():
            if value:
                indicators.add(str(key).strip().lower())
    cloud = assessment.get("cloud")
    if isinstance(cloud, dict):
        for key in ("has_docker", "has_kubernetes", "has_compose", "docker", "kubernetes"):
            value = cloud.get(key)
            if value is True or (isinstance(value, str) and value.lower() in {"true", "yes"}):
                indicators.add(key.replace("has_", ""))
        inventory = cloud.get("inventory") if isinstance(cloud.get("inventory"), dict) else {}
        for key, value in inventory.items() if isinstance(inventory, dict) else ():
            if value:
                indicators.add(str(key).strip().lower())
    facts = assessment.get("repository_facts")
    if isinstance(facts, dict):
        structure = facts.get("structure")
        if isinstance(structure, dict):
            if structure.get("has_tests"):
                indicators.add("has_tests")
    # Technology-derived service hints
    for tech in assessment.get("technologies") or []:
        if not isinstance(tech, dict):
            continue
        name = str(tech.get("name") or "").lower()
        category = str(tech.get("category") or "").lower()
        if name in {"express", "flask", "django", "fastapi", "spring boot", "laravel"}:
            indicators.add("web_application")
        if category == "library" and "openai" in name:
            indicators.add("ai_integration")
        if name == "openai":
            indicators.add("ai_integration")
    return tuple(sorted(indicators))


def _composition_facts(assessment: dict[str, Any]) -> tuple[str, ...]:
    facts_out: set[str] = set()
    facts = assessment.get("repository_facts")
    if not isinstance(facts, dict):
        return ()
    structure = facts.get("structure")
    if isinstance(structure, dict):
        for key in (
            "has_tests",
            "has_docs",
            "source_file_count",
            "test_file_count",
            "total_file_count",
        ):
            if key in structure and structure[key] is not None:
                facts_out.add(f"{key}={structure[key]}")
    build = facts.get("build")
    if isinstance(build, dict):
        systems = build.get("build_systems") or []
        if isinstance(systems, list) and systems:
            facts_out.add("has_build_system=true")
        files = build.get("build_files") or build.get("files") or []
        if isinstance(files, list) and files:
            facts_out.add(f"build_file_count={len(files)}")
    deps = facts.get("dependencies")
    if isinstance(deps, dict):
        manifests = deps.get("manifests") or []
        if isinstance(manifests, list) and manifests:
            facts_out.add(f"manifest_count={len(manifests)}")
            facts_out.add("has_dependency_manifest=true")
    return tuple(sorted(facts_out))
