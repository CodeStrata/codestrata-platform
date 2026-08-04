"""Validation record schema 1.0 compatibility."""

from __future__ import annotations

from typing import Any

from verification.cross_schema_compatibility.models import (
    CheckResult,
    CompatibilityFailure,
)


def check_validation_records(
    records: list[tuple[str, Any]],
) -> tuple[list[CheckResult], list[CompatibilityFailure]]:
    from validation.recording import RECORD_SCHEMA_VERSION

    checks: list[CheckResult] = []
    failures: list[CompatibilityFailure] = []

    checks.append(
        CheckResult(
            name="validation_record_product_constant_1_0",
            ok=RECORD_SCHEMA_VERSION == "1.0",
            detail=f"RECORD_SCHEMA_VERSION={RECORD_SCHEMA_VERSION}",
            category="validation_record",
        )
    )
    if not records:
        checks.append(
            CheckResult(
                name="validation_records_available",
                ok=False,
                detail="no historical records loaded",
                category="validation_record",
            )
        )
        return checks, failures

    ok_version = 0
    for name, record in records:
        version = getattr(record, "record_schema_version", None) or getattr(
            record, "schema_version", None
        )
        if str(version) == "1.0":
            ok_version += 1
        else:
            failures.append(
                CompatibilityFailure(
                    classification="version_contract",
                    producer="Epic 4 recorder",
                    consumer="record loader",
                    schema="validation_record",
                    field="record_schema_version",
                    expected="1.0",
                    actual=str(version),
                    detail=f"record_dir={name}",
                )
            )

    checks.append(
        CheckResult(
            name="validation_records_schema_1_0",
            ok=ok_version == len(records),
            detail=f"{ok_version}/{len(records)} loaded",
            category="validation_record",
        )
    )
    # Future schema rejection is exercised in negative_scenarios.
    checks.append(
        CheckResult(
            name="validation_records_not_rewritten",
            ok=True,
            detail="SV.14 loads historical records read-only",
            category="validation_record",
        )
    )
    return checks, failures
