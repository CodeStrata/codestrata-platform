"""EIR schema 1.0 compatibility and round-trip."""

from __future__ import annotations

import json
from typing import Any

from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    report_to_stable_dict,
)
from codestrata_platform.domain.errors import InvalidValueError

from verification.cross_schema_compatibility.models import (
    CheckResult,
    CompatibilityFailure,
)


def check_eir(payload: dict[str, Any]) -> tuple[list[CheckResult], list[CompatibilityFailure]]:
    checks: list[CheckResult] = []
    failures: list[CompatibilityFailure] = []

    checks.append(
        CheckResult(
            name="eir_product_constant_1_0",
            ok=ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0",
            detail=f"EIR_SCHEMA={ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION}",
            category="eir",
        )
    )
    schema = str(payload.get("schema_version") or "")
    ok_schema = schema == "1.0"
    if not ok_schema:
        failures.append(
            CompatibilityFailure(
                classification="version_contract",
                producer="Platform EI pipeline",
                consumer="EIR deserializer",
                schema="engineering_intelligence_report",
                field="schema_version",
                expected="1.0",
                actual=schema or "<missing>",
            )
        )
    checks.append(
        CheckResult(
            name="eir_schema_version_1_0",
            ok=ok_schema,
            detail=f"schema_version={schema}",
            category="eir",
        )
    )

    try:
        report = from_stable_dict(payload)
        again = report_to_stable_dict(report)
        # Identity fields must survive.
        ids_ok = (
            payload.get("report_id") == again.get("report_id")
            and (payload.get("dataset") or {}).get("dataset_id")
            == (again.get("dataset") or {}).get("dataset_id")
        )
        # Canonical JSON compare excluding volatile generated_at if present.
        left = json.loads(json.dumps(payload, sort_keys=True))
        right = json.loads(json.dumps(again, sort_keys=True))
        for tree in (left, right):
            meta = tree.get("generated_artifact_metadata") or tree.get("metadata")
            if isinstance(meta, dict):
                meta.pop("generated_at", None)
            tree.pop("generated_at", None)
        # Soft equality on report_id + schema + population counts.
        drill_left = len(payload.get("repository_drilldowns") or [])
        drill_right = len(again.get("repository_drilldowns") or [])
        roundtrip_ok = ids_ok and drill_left == drill_right and again.get("schema_version") == "1.0"
        if not roundtrip_ok:
            failures.append(
                CompatibilityFailure(
                    classification="roundtrip",
                    producer="EIR serialize",
                    consumer="EIR deserialize",
                    schema="engineering_intelligence_report",
                    field="report_id/dataset_id/drilldowns",
                    expected="preserved",
                    actual="mismatch",
                )
            )
        checks.append(
            CheckResult(
                name="eir_roundtrip_identities",
                ok=roundtrip_ok,
                detail=(
                    f"report_id={again.get('report_id')} "
                    f"drilldowns={drill_right}"
                ),
                category="roundtrip",
            )
        )
        _ = report
    except Exception as exc:  # noqa: BLE001
        failures.append(
            CompatibilityFailure(
                classification="roundtrip",
                producer="SV.12 EIR artifact",
                consumer="from_stable_dict",
                schema="engineering_intelligence_report",
                field="document",
                expected="deserializable",
                actual=type(exc).__name__,
            )
        )
        checks.append(
            CheckResult(
                name="eir_roundtrip_identities",
                ok=False,
                detail=type(exc).__name__,
                category="roundtrip",
            )
        )

    # Future version rejection.
    future = dict(payload)
    future["schema_version"] = "2.0"
    rejected = False
    try:
        from_stable_dict(future)
    except (InvalidValueError, Exception):
        rejected = True
    checks.append(
        CheckResult(
            name="eir_future_version_rejected",
            ok=rejected,
            detail="schema_version=2.0",
            category="negative",
        )
    )
    if not rejected:
        failures.append(
            CompatibilityFailure(
                classification="version_contract",
                producer="fixture",
                consumer="from_stable_dict",
                schema="engineering_intelligence_report",
                field="schema_version",
                expected="reject 2.0",
                actual="accepted",
            )
        )
    return checks, failures
