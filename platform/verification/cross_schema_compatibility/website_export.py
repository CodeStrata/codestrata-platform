"""Website-safe EIR export schema 1.0 compatibility."""

from __future__ import annotations

import hashlib
from typing import Any

from codestrata_platform.intelligence_reporting.application.website_export.policy import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)

from verification.cross_schema_compatibility.models import (
    CheckResult,
    CompatibilityFailure,
)


def check_website_export(
    bundle: dict[str, Any],
) -> tuple[list[CheckResult], list[CompatibilityFailure]]:
    checks: list[CheckResult] = []
    failures: list[CompatibilityFailure] = []

    checks.append(
        CheckResult(
            name="website_export_product_constant_1_0",
            ok=WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0",
            detail=f"export_schema={WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION}",
            category="website_export",
        )
    )
    manifest = bundle.get("manifest") or {}
    export_schema = str(
        manifest.get("export_schema_version") or manifest.get("schema_version") or ""
    )
    ok_schema = export_schema == "1.0"
    if not ok_schema:
        failures.append(
            CompatibilityFailure(
                classification="version_contract",
                producer="website export",
                consumer="manifest reader",
                schema="website_safe_eir_export",
                field="export_schema_version",
                expected="1.0",
                actual=export_schema or "<missing>",
            )
        )
    checks.append(
        CheckResult(
            name="website_export_schema_1_0",
            ok=ok_schema,
            detail=f"export_schema_version={export_schema}",
            category="website_export",
        )
    )

    document = bundle.get("document") or {}
    # Must not be deserializable as full EIR (allowlisted projection).
    eir_rejected = False
    try:
        from codestrata_platform.intelligence_reporting.domain.serialization import (
            from_stable_dict,
        )

        from_stable_dict(document)
    except Exception:
        eir_rejected = True
    checks.append(
        CheckResult(
            name="website_export_not_deserialized_as_full_eir",
            ok=eir_rejected,
            detail="from_stable_dict rejects website-safe projection",
            category="website_export",
        )
    )
    if not eir_rejected:
        failures.append(
            CompatibilityFailure(
                classification="projection",
                producer="website export JSON",
                consumer="EIR from_stable_dict",
                schema="website_safe_eir_export",
                field="document",
                expected="reject as full EIR",
                actual="accepted",
            )
        )

    json_text = bundle.get("json") or ""
    html_text = bundle.get("html") or ""
    # Allowlisted: must not embed findings/evidence arrays as full assessment.
    forbidden = ('"source_body"', '"file_contents"', "-----BEGIN")
    leak = [token for token in forbidden if token in json_text or token in html_text]
    checks.append(
        CheckResult(
            name="website_export_no_source_or_pem",
            ok=not leak,
            detail=f"hits={leak}",
            category="privacy",
        )
    )
    if leak:
        failures.append(
            CompatibilityFailure(
                classification="privacy",
                producer="website export",
                consumer="static artifacts",
                schema="website_safe_eir_export",
                field="projection",
                expected="no source/pem",
                actual=",".join(leak),
            )
        )

    # Manifest digests vs file bytes when present.
    artifacts = manifest.get("artifacts") or {}
    digest_ok = True
    detail = "no_artifact_digests"
    if isinstance(artifacts, dict) and artifacts:
        for name, meta in artifacts.items():
            if not isinstance(meta, dict):
                continue
            expected = meta.get("sha256")
            if not expected:
                continue
            if name.endswith(".json"):
                actual = hashlib.sha256(json_text.encode("utf-8")).hexdigest()
            elif name.endswith(".html"):
                actual = hashlib.sha256(html_text.encode("utf-8")).hexdigest()
            else:
                continue
            if actual != expected:
                digest_ok = False
                detail = f"mismatch:{name}"
                break
        else:
            detail = "digests_match"
    checks.append(
        CheckResult(
            name="website_export_manifest_digests",
            ok=digest_ok,
            detail=detail,
            category="website_export",
        )
    )
    if not digest_ok:
        failures.append(
            CompatibilityFailure(
                classification="projection",
                producer="website export",
                consumer="manifest",
                schema="website_safe_eir_export",
                field="sha256",
                expected="match file bytes",
                actual=detail,
            )
        )

    # Export is not full EIR domain object — intentional omission of internal fields.
    checks.append(
        CheckResult(
            name="website_export_uses_export_schema_fields",
            ok=bool(document.get("export_schema_version") or export_schema == "1.0"),
            detail="export_schema_version / report_schema_version (dataset_id omission intentional)",
            category="website_export",
        )
    )

    export_id = manifest.get("export_id")
    source_report = manifest.get("source_report_id")
    checks.append(
        CheckResult(
            name="website_export_ids_present",
            ok=bool(export_id) and bool(source_report),
            detail=f"export_id={export_id} source_report_id={source_report}",
            category="identifier",
        )
    )
    return checks, failures
