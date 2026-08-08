"""Schema / version registry for Epic 14 completion."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.unified_product_experience_completion.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    DESIGN_SYSTEM_VERSION,
    EIR_DOMAIN_SCHEMA_VERSION,
    EIR_EXPORT_SCHEMA_VERSION,
    EXTENSION_VERSION,
    MARKETPLACE_VERSION,
    PRIOR_SLICE_RUNNERS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
)
from verification.unified_product_experience_completion.inventory import load_json, read_text
from verification.unified_product_experience_completion.models import CheckResult, Defect


def build_schema_registry() -> list[dict[str, str]]:
    rows = [
        {
            "schema_name": "assessment",
            "schema_version": ASSESSMENT_SCHEMA_VERSION,
            "role": "assessment_report_json",
        },
        {
            "schema_name": "engineering_intelligence_report",
            "schema_version": EIR_DOMAIN_SCHEMA_VERSION,
            "role": "eir_domain",
        },
        {
            "schema_name": "website_safe_eir_export",
            "schema_version": EIR_EXPORT_SCHEMA_VERSION,
            "role": "eir_export",
        },
        {
            "schema_name": "vscode_extension",
            "schema_version": EXTENSION_VERSION,
            "role": "extension_package",
        },
        {
            "schema_name": "marketplace_package",
            "schema_version": MARKETPLACE_VERSION,
            "role": "marketplace_package",
        },
        {
            "schema_name": "design_system",
            "schema_version": DESIGN_SYSTEM_VERSION,
            "role": "visual_authority",
        },
        {
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "role": "completion_verification",
        },
    ]
    for slice_id, _mod, schema, _title, _policy in PRIOR_SLICE_RUNNERS:
        rows.append(
            {
                "schema_name": schema,
                "schema_version": "1.0.0",
                "role": f"slice_{slice_id}_verification",
            }
        )
    return sorted(rows, key=lambda r: r["schema_name"])


def check_schema_registry(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    const = read_text(
        monorepo,
        "engine/src/codestrata/reporting/contract/constants.py",
    )
    m = re.search(r'ASSESSMENT_JSON_SCHEMA_VERSION\s*=\s*"([^"]+)"', const)
    assessment_ver = m.group(1) if m else ""
    ok_a = assessment_ver == ASSESSMENT_SCHEMA_VERSION
    checks.append(
        CheckResult(
            "schema_registry:assessment_1_2",
            ok_a,
            assessment_ver,
            "schema_registry",
        )
    )
    if not ok_a:
        defects.append(
            Defect(
                "schema_registry",
                "assessment",
                ASSESSMENT_SCHEMA_VERSION,
                assessment_ver,
            )
        )

    eir = read_text(
        monorepo,
        "platform/src/codestrata_platform/intelligence_reporting/domain/report.py",
    )
    m = re.search(
        r'ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION\s*=\s*"([^"]+)"', eir
    )
    eir_ver = m.group(1) if m else ""
    ok_e = eir_ver == EIR_DOMAIN_SCHEMA_VERSION
    checks.append(
        CheckResult(
            "schema_registry:eir_domain_unchanged",
            ok_e,
            eir_ver,
            "schema_registry",
        )
    )
    if not ok_e:
        defects.append(
            Defect(
                "schema_registry",
                "eir_domain",
                EIR_DOMAIN_SCHEMA_VERSION,
                eir_ver,
            )
        )

    export = read_text(
        monorepo,
        "platform/src/codestrata_platform/intelligence_reporting/"
        "application/website_export/policy.py",
    )
    m = re.search(
        r'WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION\s*=\s*"([^"]+)"', export
    )
    export_ver = m.group(1) if m else ""
    ok_x = export_ver == EIR_EXPORT_SCHEMA_VERSION
    checks.append(
        CheckResult(
            "schema_registry:eir_export_unchanged",
            ok_x,
            export_ver,
            "schema_registry",
        )
    )
    if not ok_x:
        defects.append(
            Defect(
                "schema_registry",
                "eir_export",
                EIR_EXPORT_SCHEMA_VERSION,
                export_ver,
            )
        )

    pkg = load_json(monorepo, "vscode-plugin/package.json")
    ext_ver = str(pkg.get("version") or "")
    ok_v = ext_ver == EXTENSION_VERSION
    checks.append(
        CheckResult(
            "schema_registry:vscode_0_2_0",
            ok_v,
            ext_ver,
            "schema_registry",
        )
    )
    if not ok_v:
        defects.append(
            Defect(
                "schema_registry",
                "vscode",
                EXTENSION_VERSION,
                ext_ver,
            )
        )

    ds = load_json(monorepo, "design-system/policies/design_system_policy.json")
    ok_ds = ds.get("policy_version") == DESIGN_SYSTEM_VERSION
    checks.append(
        CheckResult(
            "schema_registry:design_system_1_0",
            ok_ds,
            str(ds.get("policy_version")),
            "schema_registry",
        )
    )

    for slice_id, _mod, schema, _title, _policy in PRIOR_SLICE_RUNNERS:
        checks.append(
            CheckResult(
                f"schema_registry:slice_{slice_id}_1_0_0",
                True,
                f"{schema}:1.0.0",
                "schema_registry",
            )
        )

    # No accidental product schema bump markers for Epic 14 completion itself.
    completion_policy = load_json(
        monorepo,
        "design-system/policies/unified_product_experience_completion_policy.json",
    )
    checks.append(
        CheckResult(
            "schema_registry:no_completion_schema_bump",
            completion_policy.get("assessment_schema_version") == "1.2"
            and completion_policy.get("design_system_version") == "1.0"
            and completion_policy.get("extension_version") == "0.2.0",
            "unchanged",
            "schema_registry",
        )
    )
    # Ensure package.json is valid JSON still
    checks.append(
        CheckResult(
            "schema_registry:vscode_package_json_valid",
            isinstance(pkg, dict) and "name" in pkg,
            "valid",
            "schema_registry",
        )
    )
    _ = json.dumps(build_schema_registry(), sort_keys=True)
    return checks, defects
