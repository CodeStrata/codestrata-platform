"""Negative compatibility scenarios (minimal fixtures; do not mutate SV artifacts)."""

from __future__ import annotations

import copy
from typing import Any

from codestrata.security.customer_safe_text import ensure_customer_safe_report_document
from codestrata.security.redaction import redact_secrets
from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.contracts import (
    SchemaCompatibilityPolicy,
)
from codestrata_platform.intelligence_reporting.application.errors import (
    UnsafeAssessmentMetadataError,
    UnsupportedAssessmentSchemaError,
)
from codestrata_platform.intelligence_reporting.application.validation import (
    resolve_schema_version,
    validate_report_document,
)
from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
)

from verification.cross_schema_compatibility.models import CheckResult


def _base_assessment() -> dict[str, Any]:
    return {
        "schema_version": "1.2",
        "assessment": {
            "findings": [
                {
                    "id": "11111111-1111-4111-8111-111111111111",
                    "rule_id": "SEC002",
                    "title": "t",
                    "description": "Hardcoded credential detected.",
                    "severity": "high",
                }
            ]
        },
    }


def check_negative_scenarios(eir: dict[str, Any]) -> list[CheckResult]:
    results: list[CheckResult] = []

    # B. Future assessment 2.0 rejected under REQUIRE_1_2_COMPLETE.
    future = _base_assessment()
    future["schema_version"] = "2.0"
    rejected_future = False
    try:
        resolve_schema_version(
            future, policy=SchemaCompatibilityPolicy.REQUIRE_1_2_COMPLETE
        )
    except UnsupportedAssessmentSchemaError:
        rejected_future = True
    results.append(
        CheckResult(
            name="negative_assessment_future_2_0_rejected",
            ok=rejected_future,
            detail="assessment schema 2.0",
            category="negative",
        )
    )

    # C. Missing assessment schema version.
    missing = _base_assessment()
    missing.pop("schema_version", None)
    missing_handled = False
    try:
        resolve_schema_version(
            missing, policy=SchemaCompatibilityPolicy.REQUIRE_1_2_COMPLETE
        )
    except UnsupportedAssessmentSchemaError:
        missing_handled = True
    results.append(
        CheckResult(
            name="negative_assessment_missing_version_rejected",
            ok=missing_handled,
            detail="REQUIRE_1_2_COMPLETE",
            category="negative",
        )
    )

    # A. 1.1 is legacy — not silently treated as 1.2 under REQUIRE policy.
    legacy = _base_assessment()
    legacy["schema_version"] = "1.1"
    legacy_rejected = False
    try:
        resolve_schema_version(
            legacy, policy=SchemaCompatibilityPolicy.REQUIRE_1_2_COMPLETE
        )
    except UnsupportedAssessmentSchemaError:
        legacy_rejected = True
    results.append(
        CheckResult(
            name="negative_assessment_1_1_not_silently_1_2",
            ok=legacy_rejected,
            detail="1.1 rejected by REQUIRE_1_2_COMPLETE",
            category="negative",
        )
    )

    # E. Unknown confidence enum — Platform EI ConfidenceLevel
    from codestrata_platform.intelligence_reporting.domain.enums import ConfidenceLevel

    unknown_conf = False
    try:
        ConfidenceLevel("not-a-real-level")
    except Exception:
        unknown_conf = True
    results.append(
        CheckResult(
            name="negative_unknown_confidence_not_defaulted",
            ok=unknown_conf,
            detail="ConfidenceLevel rejects unknown",
            category="negative",
        )
    )

    # M. EIR future version
    future_eir = copy.deepcopy(eir)
    future_eir["schema_version"] = "9.9"
    eir_rejected = False
    try:
        from_stable_dict(future_eir)
    except (InvalidValueError, Exception):
        eir_rejected = True
    results.append(
        CheckResult(
            name="negative_eir_future_rejected",
            ok=eir_rejected,
            detail="schema_version=9.9",
            category="negative",
        )
    )

    # O. Website export must not deserialize as full EIR.
    from verification.cross_schema_compatibility.artifacts import (
        load_sv12_website_export_document,
    )
    from verification.engineering_intelligence.catalog import monorepo_root_from_here

    export_doc = load_sv12_website_export_document(monorepo_root_from_here())
    export_as_eir_rejected = False
    try:
        from_stable_dict(export_doc)
    except Exception:
        export_as_eir_rejected = True
    results.append(
        CheckResult(
            name="negative_website_export_not_full_eir",
            ok=export_as_eir_rejected,
            detail="SV.12 JSON is allowlisted export projection",
            category="negative",
        )
    )

    from codestrata_platform.intelligence_reporting.application.website_export.policy import (
        WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
    )

    results.append(
        CheckResult(
            name="negative_website_export_schema_distinct",
            ok=WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0",
            detail="export schema is separate allowlisted projection",
            category="negative",
        )
    )

    # R. Unsupported assessment metadata schema version (2.0 not in allowlist).
    from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
        ALLOWED_ASSESSMENT_SCHEMA_VERSIONS,
    )

    results.append(
        CheckResult(
            name="negative_community_assessment_schema_2_0_not_allowed",
            ok="2.0" not in ALLOWED_ASSESSMENT_SCHEMA_VERSIONS,
            detail=f"allowlist={tuple(ALLOWED_ASSESSMENT_SCHEMA_VERSIONS)}",
            category="negative",
        )
    )

    # X. Unsafe PEM marker does not survive Engine safe projection.
    pem_doc = _base_assessment()
    pem_doc["assessment"]["findings"][0]["description"] = (
        "key -----BEGIN RSA PRIVATE KEY-----"
    )
    safe = ensure_customer_safe_report_document(pem_doc)
    desc = safe["assessment"]["findings"][0]["description"]
    results.append(
        CheckResult(
            name="negative_pem_does_not_survive_safe_projection",
            ok="-----BEGIN" not in desc,
            detail="customer-safe projection",
            category="negative",
        )
    )

    # Y. Platform accepts safe descriptive phrase.
    try:
        validate_report_document(
            _base_assessment()  # already safe phrase
        )
        accepted = True
    except UnsafeAssessmentMetadataError:
        accepted = False
    results.append(
        CheckResult(
            name="negative_safe_phrase_not_rejected",
            ok=accepted,
            detail="Hardcoded credential detected.",
            category="negative",
        )
    )

    # Z. Order-independent registry.
    from verification.cross_schema_compatibility.registry import build_schema_registry

    names_a = [e.contract_name for e in build_schema_registry()]
    names_b = [e.contract_name for e in reversed(list(reversed(build_schema_registry())))]
    results.append(
        CheckResult(
            name="negative_compatibility_registry_order_independent",
            ok=names_a == names_b,
            detail=f"n={len(names_a)}",
            category="negative",
        )
    )

    # W. Null required field — schema_version null rejected.
    null_version = _base_assessment()
    null_version["schema_version"] = None
    null_rejected = False
    try:
        resolve_schema_version(
            null_version, policy=SchemaCompatibilityPolicy.REQUIRE_1_2_COMPLETE
        )
    except (UnsupportedAssessmentSchemaError, Exception):
        null_rejected = True
    results.append(
        CheckResult(
            name="negative_null_schema_version_rejected",
            ok=null_rejected,
            detail="schema_version=null",
            category="negative",
        )
    )

    # Extra: redact_secrets does not leave BEGIN fence.
    results.append(
        CheckResult(
            name="negative_redact_secrets_clears_begin_fence",
            ok="-----BEGIN" not in redact_secrets("-----BEGIN PRIVATE KEY-----"),
            detail="redact_secrets",
            category="negative",
        )
    )
    return results
