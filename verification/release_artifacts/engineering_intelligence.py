"""Engineering Intelligence identity verification for SV.16."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.release_artifacts.contract import (
    AUTHORITATIVE_AGGREGATION_ID,
    AUTHORITATIVE_DATASET_ID,
    AUTHORITATIVE_EIR_ID,
    AUTHORITATIVE_EXPORT_ID,
    AUTHORITATIVE_INTERP_BUNDLE,
    AUTHORITATIVE_REPOSITORY_COUNT,
    SV12_OUTPUT_RELATIVE,
    SV13_OUTPUT_RELATIVE,
)
from verification.release_artifacts.models import CheckResult, Defect


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _identity_checks(
    *,
    label: str,
    actual: dict[str, str],
    expected: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for key, exp in expected.items():
        got = actual.get(key, "")
        ok = got == exp
        checks.append(
            CheckResult(
                name=f"engineering_intelligence:{label}:{key}",
                ok=ok,
                detail=f"expected={exp} actual={got or '<missing>'}",
                category="engineering_intelligence",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    classification="ei_identity_mismatch",
                    component=f"{label}:{key}",
                    expected=exp,
                    actual=got or "<missing>",
                )
            )
    return checks, defects


def check_engineering_intelligence(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    identities: dict[str, str] = {}

    manifest_path = monorepo / SV12_OUTPUT_RELATIVE / "export-manifest.json"
    if manifest_path.is_file():
        manifest = _read_json(manifest_path)
        repo_count = int(manifest.get("repository_count") or 0)
        checks.append(
            CheckResult(
                name="engineering_intelligence:sv12_repository_count",
                ok=repo_count == AUTHORITATIVE_REPOSITORY_COUNT,
                detail=f"count={repo_count}",
                category="engineering_intelligence",
            )
        )
        if repo_count != AUTHORITATIVE_REPOSITORY_COUNT:
            defects.append(
                Defect(
                    classification="repository_count",
                    component="sv12 export-manifest",
                    expected=str(AUTHORITATIVE_REPOSITORY_COUNT),
                    actual=str(repo_count),
                )
            )

        sv12_expected = {
            "export_id": AUTHORITATIVE_EXPORT_ID,
            "interpretation_policy_bundle_id": AUTHORITATIVE_INTERP_BUNDLE,
        }
        sv12_actual = {
            "export_id": str(manifest.get("export_id") or ""),
            "interpretation_policy_bundle_id": str(
                manifest.get("interpretation_policy_bundle_id") or ""
            ),
        }
        id_checks, id_defects = _identity_checks(
            label="sv12_manifest",
            actual=sv12_actual,
            expected=sv12_expected,
        )
        checks.extend(id_checks)
        defects.extend(id_defects)
        identities.update(sv12_actual)
    else:
        checks.append(
            CheckResult(
                name="engineering_intelligence:sv12_export_manifest",
                ok=False,
                detail="missing export-manifest.json",
                category="engineering_intelligence",
            )
        )

    sv13_report = monorepo / SV13_OUTPUT_RELATIVE / "system-defect-fixes-verification.json"
    if sv13_report.is_file():
        sv13 = _read_json(sv13_report)
        # SV.13 stores authoritative IDs at the report root (not nested).
        sv13_expected = {
            "dataset_id": AUTHORITATIVE_DATASET_ID,
            "aggregation_id": AUTHORITATIVE_AGGREGATION_ID,
            "eir_id": AUTHORITATIVE_EIR_ID,
            "interp_bundle": AUTHORITATIVE_INTERP_BUNDLE,
            "export_id": AUTHORITATIVE_EXPORT_ID,
        }
        sv13_actual = {
            "dataset_id": str(sv13.get("dataset_id") or ""),
            "aggregation_id": str(sv13.get("aggregation_id") or ""),
            "eir_id": str(sv13.get("eir_report_id") or sv13.get("eir_id") or ""),
            "interp_bundle": str(
                sv13.get("interpretation_policy_bundle_id")
                or sv13.get("interp_bundle")
                or ""
            ),
            "export_id": str(
                sv13.get("website_export_id") or sv13.get("export_id") or ""
            ),
        }
        id_checks, id_defects = _identity_checks(
            label="sv13",
            actual=sv13_actual,
            expected=sv13_expected,
        )
        checks.extend(id_checks)
        defects.extend(id_defects)
        identities.update(sv13_actual)

    eir_json = monorepo / SV12_OUTPUT_RELATIVE / "engineering-intelligence-report.json"
    if eir_json.is_file():
        payload = _read_json(eir_json)
        report_id = str(payload.get("report_id") or payload.get("eir_id") or "")
        if report_id:
            checks.append(
                CheckResult(
                    name="engineering_intelligence:sv12_eir_id",
                    ok=report_id == AUTHORITATIVE_EIR_ID,
                    detail=f"report_id={report_id}",
                    category="engineering_intelligence",
                )
            )

    return checks, defects, identities
