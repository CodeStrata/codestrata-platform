"""Catalog reconciliation against the committed Engine public catalog."""

from __future__ import annotations

import json
from pathlib import Path

from codestrata.telemetry.catalog import build_privacy_first_telemetry_catalog
from codestrata.telemetry.catalog_validation import reconcile_catalog_against_runtime

from verification.privacy_first_telemetry.models import CheckResult, Defect
from verification.privacy_first_telemetry.vscode_inputs import VsCodeTelemetryInventory


def check_catalogs(
    monorepo: Path,
    vscode: VsCodeTelemetryInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    catalog = build_privacy_first_telemetry_catalog()
    reconcile_ok = True
    try:
        reconcile_catalog_against_runtime(catalog)
    except Exception:  # noqa: BLE001
        reconcile_ok = False
    checks.append(
        CheckResult(
            name="engine_catalog_reconciles_runtime",
            ok=reconcile_ok,
            detail="build_privacy_first_telemetry_catalog + reconcile",
            category="catalog",
            client="engine",
        )
    )

    catalog_path = monorepo / "engine" / "docs" / "telemetry-event-catalog.json"
    checks.append(
        CheckResult(
            name="engine_catalog_json_committed",
            ok=catalog_path.is_file(),
            detail="engine/docs/telemetry-event-catalog.json",
            category="catalog",
            client="engine",
        )
    )
    if catalog_path.is_file():
        on_disk = json.loads(catalog_path.read_text(encoding="utf-8"))
        live = catalog.to_stable_dict()
        # Compare event names only (stable conceptual contract).
        disk_events = sorted(
            e.get("name") or e.get("event_type") or ""
            for e in on_disk.get("events", [])
        )
        live_events = sorted(
            e.get("name") or e.get("event_type") or ""
            for e in live.get("events", [])
        )
        # Filter empties
        disk_events = [e for e in disk_events if e]
        live_events = [e for e in live_events if e]
        checks.append(
            CheckResult(
                name="engine_catalog_json_matches_runtime_events",
                ok=disk_events == live_events,
                detail=f"disk={disk_events} live={live_events}",
                category="catalog",
                client="engine",
            )
        )

    mapping_src = (vscode.telemetry_dir / "catalogMapping.ts").read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            name="vscode_catalog_mapping_no_python_import",
            ok="codestrata.telemetry" not in mapping_src
            and "from codestrata" not in mapping_src
            and "import codestrata" not in mapping_src,
            detail="catalogMapping.ts does not import Engine Python",
            category="catalog",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_mapping_documents_independence",
            ok="independently versioned" in mapping_src.lower()
            or "not identical" in mapping_src.lower(),
            detail="mapping documents non-identity of schemas",
            category="catalog",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_mapping_marks_engine_only_events",
            ok="application_started" in mapping_src and "application_completed" in mapping_src,
            detail="engine-only application events documented",
            category="catalog",
            client="vscode",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="event-model-drift",
                    component=check.client,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
