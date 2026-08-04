"""Prior System Verification report gate checks for SV.16."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.release_artifacts.contract import (
    SV12_OUTPUT_RELATIVE,
    SV13_OUTPUT_RELATIVE,
    SV14_OUTPUT_RELATIVE,
    SV15_OUTPUT_RELATIVE,
)
from verification.release_artifacts.models import CheckResult, Defect, Warning

_VERIFICATION_SCHEMA_VERSION = "1.0.0"
_PASS_VERDICTS = frozenset({"PASS", "PASS_WITH_LIMITATIONS"})

_PRIOR_REPORTS: tuple[tuple[str, str], ...] = (
    ("engine/reports/verification/sv10/curated-repository-validation.json", "sv10"),
    (
        "engine/reports/verification/sv11/assessment-consistency-verification.json",
        "sv11",
    ),
    (
        f"{SV12_OUTPUT_RELATIVE}/engineering-intelligence-quality-review.json",
        "sv12_quality",
    ),
    (f"{SV13_OUTPUT_RELATIVE}/system-defect-fixes-verification.json", "sv13"),
    (f"{SV14_OUTPUT_RELATIVE}/cross-schema-compatibility-verification.json", "sv14"),
    (f"{SV15_OUTPUT_RELATIVE}/deterministic-output-verification.json", "sv15"),
)

_SV13_LEDGER = f"{SV13_OUTPUT_RELATIVE}/sv13-defect-ledger.json"


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def check_verification_reports(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[Warning]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    warnings: list[Warning] = []

    present = 0
    schema_ok = 0
    for relative, label in _PRIOR_REPORTS:
        path = monorepo / relative
        if not path.is_file():
            warnings.append(
                Warning(
                    code=f"prior_report_missing_{label}",
                    detail=f"missing {relative}",
                )
            )
            continue
        present += 1
        data = _read_json(path)
        schema_version = str(data.get("schema_version") or "")
        if schema_version == _VERIFICATION_SCHEMA_VERSION:
            schema_ok += 1
        else:
            defects.append(
                Defect(
                    classification="verification_schema",
                    component=label,
                    expected=_VERIFICATION_SCHEMA_VERSION,
                    actual=schema_version or "<missing>",
                )
            )

    checks.extend(
        [
            CheckResult(
                name="verification_reports:prior_present",
                ok=present >= 4,
                detail=f"present={present}/{len(_PRIOR_REPORTS)}",
                category="verification_reports",
            ),
            CheckResult(
                name="verification_reports:schema_1_0_0",
                ok=schema_ok == present and present > 0,
                detail=f"{schema_ok}/{present}",
                category="verification_reports",
            ),
        ]
    )

    ledger_path = monorepo / _SV13_LEDGER
    if ledger_path.is_file():
        ledger = _read_json(ledger_path)
        closed = str(
            ledger.get("closure_status")
            or ledger.get("ledger_status")
            or ledger.get("status")
            or ""
        ).lower()
        ledger_closed = closed in {"closed", "complete", "resolved"}
        checks.append(
            CheckResult(
                name="verification_reports:sv13_ledger_closed",
                ok=ledger_closed or bool(ledger.get("closed_at")),
                detail=f"status={closed or ledger.get('closed_at') or 'unknown'}",
                category="verification_reports",
            )
        )
        if not (ledger_closed or bool(ledger.get("closed_at"))):
            defects.append(
                Defect(
                    classification="verification_evidence",
                    component="sv13_ledger",
                    expected="closure_status=closed",
                    actual=closed or "<missing>",
                )
            )
    else:
        warnings.append(
            Warning(code="sv13_ledger_missing", detail=f"missing {_SV13_LEDGER}")
        )

    sv12_quality = monorepo / f"{SV12_OUTPUT_RELATIVE}/engineering-intelligence-quality-review.json"
    sv13_report = monorepo / f"{SV13_OUTPUT_RELATIVE}/system-defect-fixes-verification.json"
    if sv12_quality.is_file() and sv13_report.is_file():
        sv12 = _read_json(sv12_quality)
        sv13 = _read_json(sv13_report)
        sv12_verdict = str(sv12.get("verdict") or "").upper()
        sv13_verdict = str(sv13.get("verdict") or "").upper()
        if sv12_verdict == "FAIL" and sv13_verdict in _PASS_VERDICTS:
            checks.append(
                CheckResult(
                    name="verification_reports:sv12_fail_superseded_by_sv13",
                    ok=True,
                    detail=f"sv12={sv12_verdict} sv13={sv13_verdict}",
                    category="verification_reports",
                )
            )
        elif sv12_verdict == "FAIL":
            warnings.append(
                Warning(
                    code="sv12_fail_without_sv13_pass",
                    detail=f"sv12={sv12_verdict}; awaiting SV.13 closure",
                )
            )

    sv15_path = monorepo / f"{SV15_OUTPUT_RELATIVE}/deterministic-output-verification.json"
    if sv15_path.is_file():
        sv15 = _read_json(sv15_path)
        verdict = str(sv15.get("verdict") or "").upper()
        checks.append(
            CheckResult(
                name="verification_reports:sv15_verdict",
                ok=verdict in _PASS_VERDICTS,
                detail=f"verdict={verdict or '<missing>'}",
                category="verification_reports",
            )
        )
        if verdict and verdict not in _PASS_VERDICTS:
            defects.append(
                Defect(
                    classification="prior_verification",
                    component="sv15",
                    expected="PASS or PASS_WITH_LIMITATIONS",
                    actual=verdict,
                )
            )

    return checks, defects, warnings
