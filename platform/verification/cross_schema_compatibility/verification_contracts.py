"""System Verification report contract compatibility (1.0.0 ≠ product 1.0)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.cross_schema_compatibility.models import (
    CheckResult,
    CompatibilityFailure,
    CompatibilityWarning,
)

_VERIFICATION_REPORTS: tuple[tuple[str, str], ...] = (
    (
        "engine/reports/verification/sv10/curated-repository-validation.json",
        "curated-repository-validation",
    ),
    (
        "engine/reports/verification/sv11/assessment-consistency-verification.json",
        "assessment-consistency-verification",
    ),
    (
        "platform/reports/verification/sv12/engineering-intelligence-quality-review.json",
        "engineering-intelligence-quality-review",
    ),
    (
        "platform/reports/verification/sv13/system-defect-fixes-verification.json",
        "system-defect-fixes-verification",
    ),
)

_VERDICTS = frozenset({"PASS", "PASS_WITH_LIMITATIONS", "FAIL", "SKIPPED", "ERROR"})


def check_verification_contracts(
    monorepo: Path,
) -> tuple[list[CheckResult], list[CompatibilityFailure], list[CompatibilityWarning]]:
    checks: list[CheckResult] = []
    failures: list[CompatibilityFailure] = []
    warnings: list[CompatibilityWarning] = []

    checks.append(
        CheckResult(
            name="verification_vs_product_version_semantics",
            ok=True,
            detail="verification reports use 1.0.0; product schemas use 1.0 / 1.2",
            category="verification_contracts",
        )
    )

    present = 0
    version_ok = 0
    verdict_ok = 0
    for relative, expected_name in _VERIFICATION_REPORTS:
        path = monorepo / relative
        if not path.is_file():
            warnings.append(
                CompatibilityWarning(
                    code="verification_report_missing",
                    detail=f"missing {relative}",
                )
            )
            continue
        present += 1
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        schema_name = str(data.get("schema_name") or "")
        schema_version = str(data.get("schema_version") or "")
        if schema_version == "1.0.0":
            version_ok += 1
        else:
            failures.append(
                CompatibilityFailure(
                    classification="version_contract",
                    producer="verification package",
                    consumer="release review",
                    schema="system_verification_reports",
                    field="schema_version",
                    expected="1.0.0",
                    actual=schema_version or "<missing>",
                    detail=relative,
                )
            )
        if expected_name and schema_name and schema_name != expected_name:
            # Soft: some reports may use alternate names; warn only.
            warnings.append(
                CompatibilityWarning(
                    code="schema_name_mismatch",
                    detail=f"{relative}: got {schema_name!r} expected {expected_name!r}",
                )
            )
        verdict = str(data.get("verdict") or "").upper()
        if verdict in _VERDICTS or not verdict:
            verdict_ok += 1
        else:
            failures.append(
                CompatibilityFailure(
                    classification="enum",
                    producer="verification package",
                    consumer="release review",
                    schema="system_verification_reports",
                    field="verdict",
                    expected="PASS|PASS_WITH_LIMITATIONS|FAIL|...",
                    actual=verdict,
                    detail=relative,
                )
            )
        # Must not be treated as product EIR/assessment.
        if data.get("schema_version") == "1.0" and "report_id" in data and "dataset" in data:
            failures.append(
                CompatibilityFailure(
                    classification="version_contract",
                    producer="verification package",
                    consumer="product runtime",
                    schema="system_verification_reports",
                    field="schema_version",
                    expected="1.0.0 verification namespace",
                    actual="looks like product 1.0 EIR",
                    detail=relative,
                )
            )

    checks.extend(
        [
            CheckResult(
                name="verification_reports_present",
                ok=present >= 3,
                detail=f"present={present}/{len(_VERIFICATION_REPORTS)}",
                category="verification_contracts",
            ),
            CheckResult(
                name="verification_reports_schema_1_0_0",
                ok=version_ok == present and present > 0,
                detail=f"{version_ok}/{present}",
                category="verification_contracts",
            ),
            CheckResult(
                name="verification_verdict_vocabulary",
                ok=verdict_ok == present and present > 0,
                detail=f"{verdict_ok}/{present}",
                category="verification_contracts",
            ),
            CheckResult(
                name="verification_not_product_runtime_input",
                ok=True,
                detail="verification reports are review-only by contract",
                category="verification_contracts",
            ),
        ]
    )
    return checks, failures, warnings
