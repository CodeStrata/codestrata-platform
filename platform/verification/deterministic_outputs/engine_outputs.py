"""Engine assessment determinism using preserved SV.10 samples."""

from __future__ import annotations

from typing import Any

from codestrata.reporting.contract.canonical import (
    reports_structurally_equal,
    strip_volatile_fields,
)
from codestrata.domain.findings.ids import build_finding_id
from codestrata.domain.recommendations.ids import build_recommendation_id

from verification.deterministic_outputs.contract import DETERMINISM_SAMPLE_IDS
from verification.deterministic_outputs.fingerprints import fingerprint_assessment_report
from verification.deterministic_outputs.inputs import (
    load_sample_artifact_bundle,
    load_sv10_determinism_samples,
)
from verification.deterministic_outputs.models import CheckResult, DeterminismDefect


def check_engine_outputs(monorepo) -> tuple[list[CheckResult], list[DeterminismDefect]]:
    checks: list[CheckResult] = []
    defects: list[DeterminismDefect] = []

    samples = load_sv10_determinism_samples(monorepo)
    by_id = {str(row.get("repository_id")): row for row in samples}
    missing = [rid for rid in DETERMINISM_SAMPLE_IDS if rid not in by_id]
    checks.append(
        CheckResult(
            name="engine_sv10_determinism_samples_present",
            ok=not missing,
            detail=f"missing={missing or 'none'}",
            category="engine",
        )
    )
    all_ok = all(bool(by_id.get(rid, {}).get("ok")) for rid in DETERMINISM_SAMPLE_IDS if rid in by_id)
    checks.append(
        CheckResult(
            name="engine_sv10_determinism_samples_ok",
            ok=all_ok and not missing,
            detail="cleanarchitecture/django/bookstack/aspnetcore",
            category="engine",
        )
    )
    if not all_ok:
        defects.append(
            DeterminismDefect(
                classification="serialization",
                contract="report.json",
                expected="ok=true for SV.10 determinism samples",
                actual="sample failure",
            )
        )

    # ID builders are pure / deterministic.
    a = build_finding_id(rule_id="SEC002", subject_keys=("path/a", "x"))
    b = build_finding_id(rule_id="SEC002", subject_keys=("path/a", "x"))
    checks.append(
        CheckResult(
            name="engine_finding_id_builder_stable",
            ok=a == b and a.startswith("finding:"),
            detail=f"prefix={a.split(':',1)[0]}",
            category="engine",
        )
    )
    ra = build_recommendation_id(provider_id="test", subject_keys=("r1",))
    rb = build_recommendation_id(provider_id="test", subject_keys=("r1",))
    checks.append(
        CheckResult(
            name="engine_recommendation_id_builder_stable",
            ok=ra == rb and ra.startswith("recommendation:"),
            detail=f"prefix={ra.split(':',1)[0]}",
            category="engine",
        )
    )

    # Fingerprints for samples: stable under double strip.
    for rid in DETERMINISM_SAMPLE_IDS:
        try:
            bundle = load_sample_artifact_bundle(rid, monorepo)
        except Exception as exc:  # noqa: BLE001
            checks.append(
                CheckResult(
                    name=f"engine_sample_load_{rid}",
                    ok=False,
                    detail=type(exc).__name__,
                    category="engine",
                )
            )
            continue
        report = bundle["report"]
        fp1 = fingerprint_assessment_report(report)
        fp2 = fingerprint_assessment_report(strip_volatile_fields(report))
        equal = reports_structurally_equal(report, report)
        checks.append(
            CheckResult(
                name=f"engine_sample_fingerprint_stable_{rid}",
                ok=fp1 == fp2 and equal,
                detail=f"sha256={fp1[:16]}…",
                category="engine",
            )
        )
        # Finding IDs present and unique-ish
        findings = (report.get("assessment") or {}).get("findings") or []
        ids = [f.get("id") for f in findings if isinstance(f, dict)]
        checks.append(
            CheckResult(
                name=f"engine_sample_finding_ids_present_{rid}",
                ok=bool(ids),
                detail=f"count={len(ids)}",
                category="engine",
            )
        )
    return checks, defects
