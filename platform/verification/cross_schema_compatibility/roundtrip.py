"""Round-trip verification for supported contracts."""

from __future__ import annotations

import json
from typing import Any

from codestrata.security.customer_safe_text import ensure_customer_safe_report_document
from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    report_to_stable_dict,
)

from verification.cross_schema_compatibility.artifacts import AssessmentArtifact
from verification.cross_schema_compatibility.models import CheckResult


def check_roundtrips(
    artifacts: list[AssessmentArtifact],
    eir: dict[str, Any],
) -> list[CheckResult]:
    checks: list[CheckResult] = []

    # Assessment: serialize customer-safe → JSON → reload → IDs unchanged.
    sample = artifacts[0].report
    safe = ensure_customer_safe_report_document(sample)
    text = json.dumps(safe, sort_keys=True, separators=(",", ":"))
    reloaded = json.loads(text)
    left_ids = [
        f.get("id")
        for f in (sample.get("assessment") or {}).get("findings") or []
        if isinstance(f, dict)
    ]
    right_ids = [
        f.get("id")
        for f in (reloaded.get("assessment") or {}).get("findings") or []
        if isinstance(f, dict)
    ]
    checks.append(
        CheckResult(
            name="roundtrip_assessment_json_ids",
            ok=left_ids == right_ids and reloaded.get("schema_version") == "1.2",
            detail=f"findings={len(left_ids)} repository={artifacts[0].repository_id}",
            category="roundtrip",
        )
    )

    # EIR: serialize → deserialize → serialize identities.
    report = from_stable_dict(eir)
    again = report_to_stable_dict(report)
    checks.append(
        CheckResult(
            name="roundtrip_eir_report_id",
            ok=eir.get("report_id") == again.get("report_id"),
            detail=f"report_id={again.get('report_id')}",
            category="roundtrip",
        )
    )
    checks.append(
        CheckResult(
            name="roundtrip_eir_schema_version",
            ok=again.get("schema_version") == "1.0",
            detail=f"schema_version={again.get('schema_version')}",
            category="roundtrip",
        )
    )

    # Order independence of registry listing (determinism of SV.14 itself).
    from verification.cross_schema_compatibility.registry import build_schema_registry

    a = [e.contract_name for e in build_schema_registry()]
    b = [e.contract_name for e in build_schema_registry()]
    checks.append(
        CheckResult(
            name="roundtrip_registry_order_stable",
            ok=a == b,
            detail=f"contracts={len(a)}",
            category="roundtrip",
        )
    )
    return checks
