"""Schema registry for Epic 13 completion."""

from __future__ import annotations

from pathlib import Path

from verification.vscode_epic13_completion.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    PRIOR_SLICE_RUNNERS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
)
from verification.vscode_epic13_completion.inventory import read_text
from verification.vscode_epic13_completion.models import CheckResult, Defect


def build_schema_registry() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = [
        {
            "schema_name": "assessment",
            "schema_version": ASSESSMENT_SCHEMA_VERSION,
            "family": "product",
        },
        {
            "schema_name": "vscode-telemetry-event",
            "schema_version": "1.0",
            "family": "vscode_telemetry",
        },
        {
            "schema_name": "vscode-analytics",
            "schema_version": "1.0",
            "family": "vscode_analytics",
        },
    ]
    for slice_id, _mod, schema, _title in PRIOR_SLICE_RUNNERS:
        rows.append(
            {
                "schema_name": schema,
                "schema_version": "1.0.0",
                "family": f"epic13_{slice_id}",
            }
        )
    rows.append(
        {
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "family": "epic13_13.15",
        }
    )
    return sorted(rows, key=lambda r: r["schema_name"])


def check_schema_registry(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    # Assessment schema remains 1.2 across extension contracts
    assessment_refs = [
        "verification/vscode_assessment_execution/contract.py",
        "verification/vscode_clean_install/contract.py",
        "verification/vscode_epic13_completion/contract.py",
    ]
    for rel in assessment_refs:
        text = read_text(monorepo, rel)
        ok = f'ASSESSMENT_SCHEMA_VERSION = "{ASSESSMENT_SCHEMA_VERSION}"' in text
        checks.append(
            CheckResult(
                name=f"schema:assessment_1_2:{Path(rel).name}",
                ok=ok,
                detail=ASSESSMENT_SCHEMA_VERSION,
                category="schema_registry",
            )
        )

    # Telemetry / analytics schema files
    tel = read_text(monorepo, "vscode-plugin/src/telemetry/events.ts")
    analytics = read_text(monorepo, "vscode-plugin/src/telemetry/analytics/schema.ts")
    checks.append(
        CheckResult(
            name="schema:telemetry_events_present",
            ok="schema" in tel.lower() or "1.0" in tel,
            detail="telemetry_events",
            category="schema_registry",
        )
    )
    checks.append(
        CheckResult(
            name="schema:analytics_schema_present",
            ok="1.0" in analytics or "SCHEMA" in analytics,
            detail="analytics_schema",
            category="schema_registry",
        )
    )

    # Each prior verification schema version constant
    for slice_id, module, schema, _title in PRIOR_SLICE_RUNNERS:
        contract_rel = module.replace(".runner", ".contract").replace(".", "/") + ".py"
        # module is verification.vscode_X.runner → verification/vscode_X/contract.py
        pkg = "/".join(module.split(".")[:-1])
        contract_rel = f"{pkg}/contract.py"
        text = read_text(monorepo, contract_rel)
        ok = (
            f'SCHEMA_NAME = "{schema}"' in text
            and 'SCHEMA_VERSION = "1.0.0"' in text
        )
        checks.append(
            CheckResult(
                name=f"schema:{slice_id}:{schema}",
                ok=ok,
                detail="1.0.0" if ok else "drift",
                category="schema_registry",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    classification="prior-slice verification defect",
                    surface=contract_rel,
                    expected=f"{schema}:1.0.0",
                    observed="mismatch",
                )
            )

    checks.append(
        CheckResult(
            name="schema:completion_1_0_0",
            ok=SCHEMA_NAME == "vscode-epic13-completion-verification"
            and SCHEMA_VERSION == "1.0.0",
            detail=f"{SCHEMA_NAME}:{SCHEMA_VERSION}",
            category="schema_registry",
        )
    )

    # No shared runtime mega-schema introduced by 13.15
    mega = (monorepo / "vscode-plugin/src/epic13SharedSchema.ts").exists()
    checks.append(
        CheckResult(
            name="schema:no_shared_runtime_schema",
            ok=not mega,
            detail="absent",
            category="schema_registry",
        )
    )
    return checks, defects
