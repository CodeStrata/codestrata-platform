#!/usr/bin/env python3
"""Run the decision-ready evidence flow and enforce its report quality gates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from codestrata.application.evidence.framework.service import (
    EvidenceFrameworkService,
)

REQUIRED_ARTIFACTS = {
    "assessment.json",
    "coverage.json",
    "evidence.jsonl",
    "plan.yaml",
    "report.html",
    "report.sarif",
    "run.json",
}


def _quality_gates(result: object) -> dict[str, bool]:
    plan = result.plan
    run = result.run
    assessment = result.assessment
    evidence = result.evidence
    output = result.output_directory
    html = (output / "report.html").read_text(encoding="utf-8")
    produced = {item.name for item in output.iterdir()}
    evidence_ids = {item.evidence_id for item in evidence}
    assessment_evidence_ids = set(assessment.evidence_ids)
    return {
        "choice_fidelity": all(pack in html for pack in plan.packs)
        and all(activity.collector_id in html for activity in plan.activities),
        "producer_fidelity": all(
            item.collector_id and item.collector_version and item.payload_sha256
            for item in evidence
        ),
        "type_separation": bool(assessment.claims)
        and all(item.kind for item in evidence),
        "coverage_honesty": all(
            item.coverage.population
            and (item.coverage.planned is not None or item.coverage.limitations)
            for item in evidence
        ),
        "action_quality": bool(assessment.actions)
        and all(
            item.rationale and item.priority and item.verification
            for item in assessment.actions
        ),
        "traceability": assessment_evidence_ids <= evidence_ids
        and all(edge.source_id and edge.target_id for edge in assessment.traceability),
        "interoperability": REQUIRED_ARTIFACTS <= produced,
        "failure_isolation": run.status.value in {"completed", "partial"}
        and bool(evidence),
        "no_false_universality": "No universal repository quality score" in html,
    }


def run_repository(repository: Path, output_root: Path) -> dict[str, object]:
    service = EvidenceFrameworkService()
    catalog = service.catalog(repository)
    base = service.create_default_plan(
        repository,
        goal="Identify concrete repository health risks and guide engineering action",
    )
    plan = service.apply_packs(base, ("decision-ready-review@1.0",)).model_copy(
        update={"assessment_profile": "engineering-health-review@1.0"}
    )
    preview = service.preview(plan)
    result = service.run(plan, output_root=output_root)
    gates = _quality_gates(result)
    kinds = Counter(item.kind for item in result.evidence)
    biomarkers = [
        item.payload.get("biomarker_id")
        for item in result.evidence
        if item.kind == "code-health.biomarker"
    ]
    return {
        "repository": str(repository.resolve()),
        "repository_id": plan.subject.repository_id,
        "revision": result.run.revision,
        "detected_languages": list(catalog.detected_languages),
        "selected_packs": list(plan.packs),
        "selected_collectors": [item.collector_id for item in plan.activities],
        "preview": {
            "collectors": {
                item.collector_id: item.status for item in preview.collectors
            },
            "leaves_machine": list(preview.leaves_machine),
            "blind_spots": list(preview.blind_spots),
        },
        "run_status": result.run.status.value,
        "activity_status": {
            item.collector_id: item.status.value for item in result.run.activities
        },
        "evidence_count": len(result.evidence),
        "evidence_kinds": dict(sorted(kinds.items())),
        "biomarker_findings": dict(sorted(Counter(biomarkers).items())),
        "assessment": {
            "profile": f"{result.assessment.profile_id}@{result.assessment.profile_version}",
            "claims": len(result.assessment.claims),
            "findings": len(result.assessment.findings),
            "risks": len(result.assessment.risks),
            "actions": len(result.assessment.actions),
        },
        "quality_gates": gates,
        "quality_gate_result": "pass" if all(gates.values()) else "fail",
        "output_directory": str(result.output_directory),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repositories", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=True)
    summaries = [
        run_repository(repository, arguments.output)
        for repository in arguments.repositories
    ]
    rendered = json.dumps(summaries, indent=2, sort_keys=True)
    if arguments.summary:
        arguments.summary.parent.mkdir(parents=True, exist_ok=True)
        arguments.summary.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if all(item["quality_gate_result"] == "pass" for item in summaries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
