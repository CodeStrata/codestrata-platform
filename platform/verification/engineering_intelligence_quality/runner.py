"""SV.12 Engineering Intelligence quality review runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.engineering_intelligence.catalog import monorepo_root_from_here
from verification.engineering_intelligence_quality import (
    ENGINEERING_INTELLIGENCE_QUALITY_ID,
)
from verification.engineering_intelligence_quality.build_report import (
    build_sv12_report,
    default_sv12_output_dir,
)
from verification.engineering_intelligence_quality.capability_review import (
    review_assessment_heads,
    review_capability,
)
from verification.engineering_intelligence_quality.confidence_review import (
    review_confidence,
    review_limitations,
)
from verification.engineering_intelligence_quality.contract import (
    DATASET_DISCLAIMER,
    KNOWN_ISSUES_REPOS,
    REVIEW_JSON,
    REVIEW_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SLOW_RUNTIME_REPOS,
    SUBMODULE_LIMITATION_REPOS,
    TARGET_REPOSITORY_COUNT,
    default_contract,
)
from verification.engineering_intelligence_quality.dataset_review import review_dataset
from verification.engineering_intelligence_quality.drilldown_review import (
    review_drilldowns,
    review_provenance,
)
from verification.engineering_intelligence_quality.inputs import (
    load_prepared_assessments_from_sv10,
    resolve_sv10_dir,
)
from verification.engineering_intelligence_quality.models import (
    DefectCandidate,
    EditorialObservation,
    QualityReviewReport,
)
from verification.engineering_intelligence_quality.modernization_review import (
    review_modernization,
)
from verification.engineering_intelligence_quality.pattern_review import review_patterns
from verification.engineering_intelligence_quality.reporting import (
    signal_to_noise_summary,
    write_review_markdown,
)
from verification.engineering_intelligence_quality.safety import review_safety
from verification.engineering_intelligence_quality.technology_review import review_technology
from verification.engineering_intelligence_quality.usefulness_review import review_usefulness
from verification.engineering_intelligence_quality.wording_review import review_wording


def _sv10_limitations(monorepo: Path) -> dict[str, list[str]]:
    sv10 = resolve_sv10_dir(monorepo)
    out: dict[str, list[str]] = {}
    for path in sorted((sv10 / "records").glob("*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        out[path.stem] = [str(x) for x in (row.get("limitations") or [])]
    return out


def _special_case_review(
    included: list[str],
    sv10_lims: dict[str, list[str]],
    *,
    rejected: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    notes: list[str] = []
    for rid in sorted(set(included) & KNOWN_ISSUES_REPOS):
        notes.append(
            f"{rid}: intentionally vulnerable/demo posture — do not treat pattern "
            "prevalence as ordinary software risk without limitation"
        )
    for rid in sorted(set(included) & SUBMODULE_LIMITATION_REPOS):
        notes.append(
            f"{rid}: submodules not initialized (SV.10); coverage limitations must remain visible"
        )
    for rid in sorted(set(included) & SLOW_RUNTIME_REPOS):
        notes.append(
            f"{rid}: Tier 3 runtime over 10m — not technical-debt severity or product inaccuracy"
        )
    for row in rejected or []:
        notes.append(
            f"{row.get('repository_id')}: rejected by Platform EI ingestion "
            f"({row.get('reason')}: {row.get('detail')})"
        )
    return {
        "ok": not bool(rejected),
        "notes": notes,
        "rejected_repositories": rejected or [],
        "summary": (
            f"{len(notes)} special-case notes; "
            f"{len(rejected or [])} ingestion rejections"
        ),
    }


def _verdict(defects: list[DefectCandidate], observations: list[EditorialObservation]) -> str:
    if any(d.release_impact == "blocking" for d in defects):
        return "FAIL"
    material = [d for d in defects if d.release_impact == "material"]
    material_obs = [
        o
        for o in observations
        if o.release_impact == "material" and o.classification in {
            "misleading",
            "product_defect_candidate",
            "insufficient_support",
        }
    ]
    if material or material_obs:
        # Material editorial gaps → PASS_WITH_LIMITATIONS if not product defects
        if any(d.recommended_handling == "SV.13_product_fix" for d in material):
            return "FAIL"
        return "PASS_WITH_LIMITATIONS"
    if observations or defects:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def run_engineering_intelligence_quality(
    *,
    monorepo: Path | None = None,
    output_dir: Path | None = None,
) -> QualityReviewReport:
    contract = default_contract()
    root = (monorepo or monorepo_root_from_here()).resolve()
    out = (output_dir or default_sv12_output_dir(root)).resolve()

    assessments, sv11, meta = load_prepared_assessments_from_sv10(monorepo=root)
    built = build_sv12_report(assessments, output_dir=out, monorepo=root)
    payload = built.report_payload
    expected_ids = [a.repository_id for a in assessments]
    sv10_lims = _sv10_limitations(root)

    rejected_rows: list[dict[str, str]] = []
    ingest = built.pipeline.ingest_result
    for snap in getattr(ingest, "rejected", ()) or ():
        rid = str(getattr(snap, "repository_id", "")).removeprefix("repo:")
        detail = ""
        for diag in getattr(ingest, "diagnostics", ()) or ():
            if getattr(diag, "repository_id", "") == f"repo:{rid}" or getattr(diag, "repository_id", "") == rid:
                detail = str(getattr(diag, "message", "") or diag)[:160]
                break
        rejected_rows.append(
            {
                "repository_id": rid,
                "reason": str(getattr(snap, "exclusion_reason", "") or "rejected"),
                "detail": detail or str(getattr(snap, "limitations", "")),
            }
        )

    all_obs: list[EditorialObservation] = []
    all_defects: list[DefectCandidate] = []

    dataset_review, obs, defs = review_dataset(
        payload, expected_ids=expected_ids, sv10_limitations=sv10_lims
    )
    all_obs.extend(obs)
    all_defects.extend(defs)

    tech_review, obs, defs = review_technology(payload)
    all_obs.extend(obs)
    all_defects.extend(defs)

    cap_review, obs, defs = review_capability(payload)
    all_obs.extend(obs)
    all_defects.extend(defs)

    head_review, obs, defs = review_assessment_heads(payload)
    all_obs.extend(obs)
    all_defects.extend(defs)

    pattern_review, obs, defs = review_patterns(payload)
    all_obs.extend(obs)
    all_defects.extend(defs)

    mod_review, obs, defs = review_modernization(payload)
    all_obs.extend(obs)
    all_defects.extend(defs)

    conf_review, obs, defs = review_confidence(payload)
    all_obs.extend(obs)
    all_defects.extend(defs)

    lim_review, obs, defs = review_limitations(payload, included_ids=expected_ids)
    all_obs.extend(obs)
    all_defects.extend(defs)

    drill_review, obs, defs = review_drilldowns(payload, expected_ids=expected_ids)
    all_obs.extend(obs)
    all_defects.extend(defs)

    prov_review, obs, defs = review_provenance(payload)
    all_obs.extend(obs)
    all_defects.extend(defs)

    wording, obs, defs = review_wording(json_text=built.json_text, html_text=built.html_text)
    all_obs.extend(obs)
    all_defects.extend(defs)

    special = _special_case_review(
        expected_ids, sv10_lims, rejected=rejected_rows
    )
    use_review, audiences, obs = review_usefulness(
        payload, special_case_notes=special.get("notes") or []
    )
    all_obs.extend(obs)

    safe_review, obs, defs = review_safety(
        output_dir=out,
        json_text=built.json_text,
        html_text=built.html_text,
        manifest_payload=built.manifest_payload,
    )
    all_obs.extend(obs)
    all_defects.extend(defs)

    stn = signal_to_noise_summary(
        payload,
        json_bytes=len(built.export.json_bytes),
        html_bytes=len(built.export.html_bytes),
    )

    dataset_id = None
    if isinstance(payload.get("dataset"), dict):
        dataset_id = payload["dataset"].get("dataset_id")
    export_id = None
    if isinstance(built.manifest_payload, dict):
        export_id = (
            built.manifest_payload.get("export_id")
            or built.manifest_payload.get("website_export_id")
            or built.manifest_payload.get("id")
        )

    verdict = _verdict(all_defects, all_obs)
    # Curated OSS + known limitations always at least PASS_WITH_LIMITATIONS when otherwise clean.
    if verdict == "PASS":
        verdict = "PASS_WITH_LIMITATIONS"

    report = QualityReviewReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=ENGINEERING_INTELLIGENCE_QUALITY_ID,
        catalog_id=meta.catalog_id,
        repository_count=TARGET_REPOSITORY_COUNT,
        dataset_id=dataset_id,
        eir_report_id=str(payload.get("report_id") or ""),
        interpretation_policy_bundle_id=str(
            payload.get("interpretation_policy_bundle_id") or ""
        ),
        website_export_id=str(export_id) if export_id else None,
        included_repository_ids=sorted(expected_ids),
        dataset_review=dataset_review,
        technology_distribution_review=tech_review,
        capability_comparison_review=cap_review,
        assessment_head_review=head_review,
        recurring_pattern_review=pattern_review,
        modernization_observation_review=mod_review,
        confidence_review=conf_review,
        limitation_review=lim_review,
        repository_drilldown_review=drill_review,
        provenance_review=prov_review,
        wording_review=wording,
        usability_review=use_review,
        commercial_usefulness=[a.to_dict() for a in audiences],
        signal_to_noise=stn,
        website_safe_review=safe_review,
        special_case_review=special,
        defect_candidates=[d.to_dict() for d in all_defects],
        editorial_observations=[o.to_dict() for o in all_obs],
        limitations=[
            DATASET_DISCLAIMER,
            *contract.notes,
            f"SV.11 gate verdict={sv11.get('verdict')}",
            *special.get("notes", [])[:8],
        ],
        warnings=[],
        verdict=verdict,
    )
    report.write_json(out / REVIEW_JSON)
    write_review_markdown(report, out / REVIEW_MD)
    return report
