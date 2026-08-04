"""Load preserved SV.10–SV.13 artifacts for SV.14 (no clone/reassess)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from verification.engineering_intelligence.catalog import monorepo_root_from_here
from verification.cross_schema_compatibility.contract import (
    CATALOG_RELATIVE,
    SV10_OUTPUT_RELATIVE,
    SV11_REPORT_RELATIVE,
    SV12_OUTPUT_RELATIVE,
    SV13_LEDGER_RELATIVE,
    TARGET_REPOSITORY_COUNT,
    VALIDATION_SUMMARY_RELATIVE,
)


class Sv14ArtifactError(RuntimeError):
    """Raised when required preserved artifacts are missing."""


@dataclass(frozen=True, slots=True)
class AssessmentArtifact:
    repository_id: str
    report_path_relative: str
    report: dict[str, Any]
    findings: dict[str, Any] | list[Any] | None
    recommendations: dict[str, Any] | list[Any] | None


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_assessment_artifacts(
    monorepo: Path | None = None,
) -> list[AssessmentArtifact]:
    root = (monorepo or monorepo_root_from_here()).resolve()
    sv10 = root / SV10_OUTPUT_RELATIVE
    records_dir = sv10 / "records"
    if not records_dir.is_dir():
        raise Sv14ArtifactError(f"missing SV.10 records: {SV10_OUTPUT_RELATIVE}/records")

    artifacts: list[AssessmentArtifact] = []
    for record_path in sorted(records_dir.glob("*.json")):
        record = _read_json(record_path)
        repository_id = str(record.get("repository_id") or record_path.stem)
        sha = str(record.get("final_checkout_sha") or "")
        run_dir = sv10 / "artifacts" / repository_id / sha[:12]
        if not (run_dir / "report.json").is_file():
            matches = sorted((sv10 / "artifacts" / repository_id).glob("*/report.json"))
            if len(matches) != 1:
                raise Sv14ArtifactError(f"missing report.json for {repository_id}")
            run_dir = matches[0].parent
        report = _read_json(run_dir / "report.json")
        findings = None
        recommendations = None
        if (run_dir / "findings.json").is_file():
            findings = _read_json(run_dir / "findings.json")
        if (run_dir / "recommendations.json").is_file():
            recommendations = _read_json(run_dir / "recommendations.json")
        rel = str(run_dir.relative_to(root))
        artifacts.append(
            AssessmentArtifact(
                repository_id=repository_id,
                report_path_relative=f"{rel}/report.json",
                report=report,
                findings=findings,
                recommendations=recommendations,
            )
        )
    if len(artifacts) != TARGET_REPOSITORY_COUNT:
        raise Sv14ArtifactError(
            f"expected {TARGET_REPOSITORY_COUNT} assessments, found {len(artifacts)}"
        )
    return artifacts


def load_sv12_website_export_document(monorepo: Path | None = None) -> dict[str, Any]:
    """Load the SV.12 on-disk JSON (website-safe export projection, not full EIR)."""

    root = (monorepo or monorepo_root_from_here()).resolve()
    path = root / SV12_OUTPUT_RELATIVE / "engineering-intelligence-report.json"
    if not path.is_file():
        raise Sv14ArtifactError("missing SV.12 engineering-intelligence-report.json")
    data = _read_json(path)
    if not isinstance(data, dict):
        raise Sv14ArtifactError("website export JSON must be an object")
    return data


def build_full_eir_from_sv10(monorepo: Path | None = None) -> dict[str, Any]:
    """Rebuild full EIR domain payload from preserved SV.10 assessments.

    SV.12 writes the website-safe projection to disk; the full EIR is rebuilt
    here for schema 1.0 round-trip verification without reassessment.
    """

    from verification.engineering_intelligence_quality.inputs import (
        load_prepared_assessments_from_sv10,
    )
    from verification.engineering_intelligence.ingestion import (
        build_pipeline_from_assessments,
    )

    root = (monorepo or monorepo_root_from_here()).resolve()
    assessments, _sv11, _meta = load_prepared_assessments_from_sv10(monorepo=root)
    pipeline = build_pipeline_from_assessments(
        assessments,
        title="SV.14 Cross-Schema Compatibility EIR",
    )
    return pipeline.report_payload


# Back-compat alias used by early SV.14 drafts — prefer build_full_eir_from_sv10.
def load_sv12_eir(monorepo: Path | None = None) -> dict[str, Any]:
    return build_full_eir_from_sv10(monorepo)


def load_sv12_export_bundle(monorepo: Path | None = None) -> dict[str, Any]:
    root = (monorepo or monorepo_root_from_here()).resolve()
    base = root / SV12_OUTPUT_RELATIVE
    return {
        "json": (base / "engineering-intelligence-report.json").read_text(encoding="utf-8"),
        "html": (base / "engineering-intelligence-report.html").read_text(encoding="utf-8"),
        "manifest": _read_json(base / "export-manifest.json"),
        "quality_review": _read_json(
            base / "engineering-intelligence-quality-review.json"
        ),
        "document": load_sv12_website_export_document(root),
    }


def load_sv11_report(monorepo: Path | None = None) -> dict[str, Any]:
    root = (monorepo or monorepo_root_from_here()).resolve()
    path = root / SV11_REPORT_RELATIVE
    if not path.is_file():
        raise Sv14ArtifactError("missing SV.11 assessment-consistency-verification.json")
    return _read_json(path)


def load_sv13_ledger(monorepo: Path | None = None) -> dict[str, Any]:
    root = (monorepo or monorepo_root_from_here()).resolve()
    path = root / SV13_LEDGER_RELATIVE
    if not path.is_file():
        raise Sv14ArtifactError("missing SV.13 defect ledger")
    return _read_json(path)


def load_validation_summary(monorepo: Path | None = None) -> dict[str, Any] | None:
    root = (monorepo or monorepo_root_from_here()).resolve()
    path = root / VALIDATION_SUMMARY_RELATIVE
    if not path.is_file():
        return None
    data = _read_json(path)
    return data if isinstance(data, dict) else None


def load_sample_validation_records(
    monorepo: Path | None = None,
    *,
    limit: int = 5,
) -> list[tuple[str, Any]]:
    """Load up to ``limit`` latest validation records without rewriting them."""

    root = (monorepo or monorepo_root_from_here()).resolve()
    results = root / "engine" / "validation" / "results"
    if not results.is_dir():
        return []

    import sys

    engine = str(root / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    from validation.recording import load_repository_validation_record

    loaded: list[tuple[str, Any]] = []
    for latest in sorted(results.glob("*/latest")):
        if not (latest / "record.json").is_file():
            continue
        try:
            record = load_repository_validation_record(latest)
        except Exception:  # noqa: BLE001 - skip unreadable historical dirs
            continue
        loaded.append((latest.parent.name, record))
        if len(loaded) >= limit:
            break
    return loaded


def catalog_release_validation_count(monorepo: Path | None = None) -> int:
    root = (monorepo or monorepo_root_from_here()).resolve()
    catalog = _read_json(root / CATALOG_RELATIVE)
    count = 0
    for item in catalog.get("repositories") or []:
        enabled = item.get("enabled_for") or {}
        if enabled.get("release_validation"):
            count += 1
    return count
