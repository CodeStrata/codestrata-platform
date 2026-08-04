"""SV.8 website-export verification runner."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from codestrata_platform.intelligence_reporting.application.website_export import (
    HTML_FILENAME,
    JSON_FILENAME,
    MANIFEST_FILENAME,
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.application.website_export.manifest import (
    sha256_bytes,
)

from verification.website_export.accessibility import check_accessibility
from verification.website_export.contract import (
    HTML_FILENAME as _HF,
    JSON_FILENAME as _JF,
    MANIFEST_FILENAME as _MF,
    default_contract,
)
from verification.website_export.determinism import check_determinism
from verification.website_export.html_export import check_html_export
from verification.website_export.inputs import (
    build_verified_export,
    verify_source_eir,
)
from verification.website_export.json_export import check_json_export
from verification.website_export.manifest import check_manifest
from verification.website_export.models import CheckResult, VerificationReport
from verification.website_export.parity import check_parity
from verification.website_export.projection import (
    check_export_identity,
    check_export_policy,
    check_projection,
    check_reproject_same_document,
)
from verification.website_export.reporting import write_verification_report
from verification.website_export.safety import check_safety
from verification.website_export.scenarios import (
    check_anonymized_scope,
    check_identity_alias_stability,
    check_oss_demonstration_regression,
    check_policy_token_required,
    check_unsafe_text_rejection,
    check_writer_partial_failure_contract,
)
from verification.website_export.writer import check_writer


def run_website_export_verification(
    *,
    output_dir: Path | None = None,
    cache_dir: Path | None = None,
    with_catalog_network: bool = False,
) -> VerificationReport:
    started = time.perf_counter()
    contract = default_contract()
    out = (
        output_dir
        or Path(__file__).resolve().parents[2] / "reports" / "verification"
    ).resolve()
    out.mkdir(parents=True, exist_ok=True)

    verified = build_verified_export(
        cache_dir=cache_dir,
        with_catalog_network=with_catalog_network,
        generated_at=None,
    )
    checks: list[CheckResult] = []
    checks.extend(verify_source_eir(verified.report))
    checks.extend(check_export_policy(verified))
    checks.extend(check_projection(verified))
    checks.extend(check_reproject_same_document(verified))
    checks.extend(check_export_identity(verified))
    checks.extend(check_json_export(verified))
    checks.extend(check_html_export(verified))
    checks.extend(check_parity(verified))
    checks.extend(check_manifest(verified))
    checks.extend(check_accessibility(verified))
    checks.extend(check_determinism(verified))
    checks.extend(check_safety(verified))
    checks.extend(check_identity_alias_stability(verified))
    checks.extend(check_anonymized_scope(verified))
    checks.extend(check_unsafe_text_rejection())
    checks.extend(check_policy_token_required(verified))
    checks.extend(check_oss_demonstration_regression())

    with tempfile.TemporaryDirectory(prefix="sv8-website-export-") as tmp:
        tmp_path = Path(tmp)
        checks.extend(check_writer(verified, tmp_path))
        checks.extend(check_writer_partial_failure_contract(tmp_path / "partial-root", verified))

    # Filename allowlist sanity (verification contract mirrors product constants).
    checks.append(
        CheckResult(
            name="contract:artifact_filenames",
            ok=(
                JSON_FILENAME == _JF == "engineering-intelligence-report.json"
                and HTML_FILENAME == _HF == "engineering-intelligence-report.html"
                and MANIFEST_FILENAME == _MF == "export-manifest.json"
            ),
            detail="allowlisted filenames",
            category="contract",
        )
    )

    failures = [f"{c.name}:{c.detail}" for c in checks if not c.ok]
    by_category: dict[str, int] = {}
    for item in checks:
        by_category[item.category] = by_category.get(item.category, 0) + (
            0 if item.ok else 1
        )

    meta = verified.bundle.document.export_metadata
    assert meta is not None
    report = VerificationReport(
        ok=not failures,
        verdict="pass" if not failures else "fail",
        source_report_id=verified.report.report_id.value,
        source_dataset_id=verified.report.dataset.dataset_id.value,
        interpretation_policy_bundle_id=verified.report.interpretation_policy_bundle_id,
        export_policy_token=verified.policy.policy_token,
        website_export_schema_version=WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
        export_id=meta.export_id,
        scope=verified.bundle.document.scope,
        repository_count=int(
            verified.bundle.document.dataset_summary.get("repository_count", 0)
        ),
        artifact_inventory=(JSON_FILENAME, HTML_FILENAME, MANIFEST_FILENAME),
        json_digest=sha256_bytes(verified.bundle.json_bytes),
        html_digest=sha256_bytes(verified.bundle.html_bytes),
        checks=tuple(checks),
        scenario_summary={
            "total_checks": len(checks),
            "failed_checks": len(failures),
            **{f"failed_{k}": v for k, v in by_category.items() if v},
        },
        defects=tuple(failures),
        limitations=tuple(contract.notes),
        elapsed_ms=(time.perf_counter() - started) * 1000,
    )
    write_verification_report(report, out)
    return report
