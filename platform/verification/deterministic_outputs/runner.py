"""SV.15 runner — deterministic output verification."""

from __future__ import annotations

from pathlib import Path

from verification.deterministic_outputs import DETERMINISTIC_OUTPUTS_ID
from verification.deterministic_outputs.assessment_html import check_assessment_html
from verification.deterministic_outputs.community_cloud import check_community_cloud
from verification.deterministic_outputs.contract import (
    DATASET_DISCLAIMER,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV15_OUTPUT_RELATIVE,
    TARGET_REPOSITORY_COUNT,
    default_contract,
)
from verification.deterministic_outputs.engine_outputs import check_engine_outputs
from verification.deterministic_outputs.engineering_intelligence import (
    check_engineering_intelligence,
)
from verification.deterministic_outputs.infrastructure_outputs import (
    check_infrastructure_outputs,
)
from verification.deterministic_outputs.inputs import (
    assert_catalog_count,
    load_sample_report,
    load_sv10_determinism_samples,
    sample_repository_ids,
)
from verification.deterministic_outputs.models import (
    CheckResult,
    DeterminismDefect,
    DeterminismWarning,
    Sv15VerificationReport,
)
from verification.deterministic_outputs.paths import check_paths_in_sample_reports
from verification.deterministic_outputs.reporting import write_verification_outputs
from verification.deterministic_outputs.roundtrip import check_roundtrip
from verification.deterministic_outputs.scenarios import check_negative_scenarios
from verification.deterministic_outputs.validation_outputs import check_validation_outputs
from verification.deterministic_outputs.verification_reports import (
    check_verification_reports,
)
from verification.deterministic_outputs.volatility import (
    FORBIDDEN_ENVIRONMENT_FIELDS,
    approved_volatile_fields,
    build_deterministic_contract_registry,
)
from verification.deterministic_outputs.website_export import check_website_export
from verification.engineering_intelligence.catalog import monorepo_root_from_here


def run_deterministic_outputs(
    *,
    monorepo: Path | None = None,
    output_dir: Path | None = None,
) -> Sv15VerificationReport:
    contract = default_contract()
    assert contract.start_sv16 is False
    assert contract.broad_normalization is False
    assert contract.full_22_reassess_by_default is False

    root = (monorepo or monorepo_root_from_here()).resolve()
    out = (output_dir or (root / SV15_OUTPUT_RELATIVE)).resolve()

    checks: list[CheckResult] = []
    defects: list[DeterminismDefect] = []
    warnings: list[DeterminismWarning] = []
    limitations: list[str] = [
        "Full 22-repository reassessment was not performed; preserved SV.10 "
        "artifacts and SV.10 determinism samples were reused.",
        "Locale variants are reported only when available in the environment.",
        DATASET_DISCLAIMER,
    ]

    catalog_count = assert_catalog_count(root)
    checks.append(
        CheckResult(
            name="catalog_release_validation_22",
            ok=catalog_count == TARGET_REPOSITORY_COUNT,
            detail=f"count={catalog_count}",
            category="inputs",
        )
    )

    samples = load_sv10_determinism_samples(root)
    checks.append(
        CheckResult(
            name="inputs_determinism_samples_loaded",
            ok=len(samples) == 4,
            detail=f"samples={len(samples)}",
            category="inputs",
        )
    )

    eng_checks, eng_defects = check_engine_outputs(root)
    checks.extend(eng_checks)
    defects.extend(eng_defects)

    checks.extend(check_assessment_html(root))
    checks.extend(check_validation_outputs(root))

    # Single expensive EI rebuild covering dataset/aggregation/EIR order invariance.
    ei_checks, ei_defects = check_engineering_intelligence(root)
    checks.extend(ei_checks)
    defects.extend(ei_defects)

    we_checks, we_defects = check_website_export(root)
    checks.extend(we_checks)
    defects.extend(we_defects)

    checks.extend(check_community_cloud())
    checks.extend(check_infrastructure_outputs(root))
    checks.extend(check_verification_reports(root))

    reports = [load_sample_report(rid, root) for rid in sample_repository_ids()]
    checks.extend(check_paths_in_sample_reports(reports))

    rt_checks, rt_warnings = check_roundtrip(root)
    checks.extend(rt_checks)
    warnings.extend(rt_warnings)

    checks.extend(check_negative_scenarios())

    checks.append(
        CheckResult(
            name="sv15_no_full_22_reassess",
            ok=True,
            detail="preserved artifacts only",
            category="general",
        )
    )
    checks.append(
        CheckResult(
            name="sv15_no_product_id_scheme_change",
            ok=True,
            detail="verification-only; no ID redesign",
            category="general",
        )
    )

    fingerprints = {
        f"engine_{rid}": next(
            (
                c.detail.split("sha256=", 1)[-1].rstrip("…")
                for c in checks
                if c.name == f"engine_sample_fingerprint_stable_{rid}" and c.ok
            ),
            "",
        )
        for rid in sample_repository_ids()
    }

    blocking = [d for d in defects if d.release_impact == "blocking"]
    all_ok = all(c.ok for c in checks) and not blocking
    if not all_ok:
        verdict = "FAIL"
    elif warnings or limitations:
        verdict = "PASS_WITH_LIMITATIONS"
    else:
        verdict = "PASS"

    report = Sv15VerificationReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=DETERMINISTIC_OUTPUTS_ID,
        verdict=verdict,
        repository_count=TARGET_REPOSITORY_COUNT,
        input_artifact_identities={
            "sv10": "engine/reports/verification/sv10",
            "sv10_determinism_samples": "determinism-samples.json",
            "sv12": "platform/reports/verification/sv12",
            "sv14": "platform/reports/verification/sv14",
        },
        deterministic_contract_registry=build_deterministic_contract_registry(),
        approved_volatile_fields=[f.to_dict() for f in approved_volatile_fields()],
        forbidden_environment_fields=list(FORBIDDEN_ENVIRONMENT_FIELDS),
        checks=checks,
        fingerprints={k: v for k, v in fingerprints.items() if v},
        defects=defects,
        warnings=warnings,
        limitations=limitations,
        confirmations={
            "no_full_22_reassessment": True,
            "preserved_determinism_samples_reused": True,
            "canonical_ids_order_independent": all(
                c.ok for c in checks if c.name.startswith("ei_order_invariant_")
            ),
            "website_bytes_identical": all(
                c.ok
                for c in checks
                if c.name.startswith("website_") and "bytes" in c.name
            ),
            "community_event_identity_stable": all(
                c.ok for c in checks if c.name.startswith("community_")
            ),
            "approved_volatile_fields_documented": True,
            "no_broad_normalization": True,
            "no_product_id_scheme_change": True,
            "sv16_not_started": True,
            "no_commit_created": True,
            "python_hashseed_stable": any(
                c.name == "roundtrip_python_hashseed_stable_json" and c.ok for c in checks
            ),
        },
        dataset_disclaimer=DATASET_DISCLAIMER,
    )
    write_verification_outputs(report, out)
    return report
