"""Catalog / preview / status completion checks and determinism."""

from __future__ import annotations

from pathlib import Path

from codestrata.telemetry.catalog import build_privacy_first_telemetry_catalog
from codestrata.telemetry.catalog_formatting import format_catalog_json, format_catalog_markdown
from codestrata.telemetry.catalog_write import catalog_artifact_paths
from codestrata.telemetry.preview_builder import build_privacy_first_telemetry_preview
from codestrata.telemetry.runtime_factory import create_default_telemetry_runtime

from verification.privacy_first_telemetry_completion.models import CheckResult, Defect


def check_catalog_preview_status(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    catalog = build_privacy_first_telemetry_catalog()
    checks.append(
        CheckResult(
            name="catalog_five_events",
            ok=len(catalog.events) == 5,
            detail=f"events={len(catalog.events)}",
            category="catalog",
        )
    )
    checks.append(
        CheckResult(
            name="catalog_transmission_not_operational",
            ok=getattr(catalog, "transmission_status", "not_operational")
            in ("not_operational", "unavailable", None)
            or str(getattr(catalog, "transmission_status", "")).lower()
            in ("not_operational", "unavailable", ""),
            detail=str(getattr(catalog, "transmission_status", "")),
            category="catalog",
        )
    )

    docs = monorepo / "engine" / "docs"
    json_path, md_path = catalog_artifact_paths(docs_dir=docs)
    expected_json = format_catalog_json(catalog)
    expected_md = format_catalog_markdown(catalog)
    checks.append(
        CheckResult(
            name="catalog_artifacts_match_builder",
            ok=json_path.read_text(encoding="utf-8") == expected_json
            and md_path.read_text(encoding="utf-8") == expected_md,
            detail="JSON/Markdown match builder",
            category="catalog",
        )
    )

    preview = build_privacy_first_telemetry_preview()
    stable = preview.to_stable_dict()
    checks.append(
        CheckResult(
            name="preview_local_only",
            ok=stable.get("transmission_performed") is False
            and stable.get("transport_status") == "unavailable",
            detail="preview no transport",
            category="preview",
        )
    )
    checks.append(
        CheckResult(
            name="preview_no_installation_identity",
            ok=stable.get("installation_identity_used") is False,
            detail="installation_identity_used=False",
            category="preview",
        )
    )
    p1 = preview.to_stable_json()
    p2 = build_privacy_first_telemetry_preview().to_stable_json()
    checks.append(
        CheckResult(
            name="preview_deterministic",
            ok=p1 == p2,
            detail="preview JSON identical",
            category="preview",
        )
    )

    runtime = create_default_telemetry_runtime()
    diag = runtime.diagnostics().to_stable_dict()
    checks.append(
        CheckResult(
            name="status_diagnostics_side_effect_free_keys",
            ok="installation_id" not in diag and "endpoint" not in diag,
            detail="diagnostics bounded",
            category="status",
        )
    )

    vscode_preview = monorepo / "vscode-plugin" / "src" / "telemetry" / "preview.ts"
    vs = vscode_preview.read_text(encoding="utf-8") if vscode_preview.is_file() else ""
    checks.append(
        CheckResult(
            name="vscode_preview_internal",
            ok="buildVsCodeTelemetryPreview" in vs and "transmissionPerformed: false" in vs,
            detail="internal preview",
            category="preview",
        )
    )

    statuses = {
        "catalog_status": "pass" if all(c.ok for c in checks if c.category == "catalog") else "fail",
        "preview_status": "pass" if all(c.ok for c in checks if c.category == "preview") else "fail",
        "status_command_status": (
            "pass" if all(c.ok for c in checks if c.category == "status") else "fail"
        ),
    }

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="privacy defect",
                    component=check.category,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects, statuses


def check_determinism(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    from verification.privacy_first_telemetry_completion.versions import (
        build_policy_registry,
        build_schema_registry,
    )

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    a = build_policy_registry()
    b = build_policy_registry()
    checks.append(
        CheckResult(
            name="policy_registry_deterministic",
            ok=a == b,
            detail="policy registry identical",
            category="determinism",
        )
    )
    s1 = build_schema_registry()
    s2 = build_schema_registry()
    checks.append(
        CheckResult(
            name="schema_registry_deterministic",
            ok=s1 == s2,
            detail="schema registry identical",
            category="determinism",
        )
    )
    _ = monorepo
    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="harness defect",
                    component="determinism",
                    expected="pass",
                    actual=check.name,
                )
            )
    return checks, defects
