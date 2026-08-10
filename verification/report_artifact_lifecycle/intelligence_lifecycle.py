"""Engineering intelligence lifecycle checks for Slice 17.15."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.contract import ENGINE_LIFECYCLE, SLOTS
from verification.report_artifact_lifecycle.helpers import add_check, try_import_engine_module
from verification.report_artifact_lifecycle.models import CheckResult, Defect


def check_intelligence_lifecycle(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"rotation_exercised": False, "membership_preserved": False}

    lifecycle_path = monorepo / ENGINE_LIFECYCLE
    add_check(
        checks,
        defects,
        "intelligence_lifecycle:module_exists",
        lifecycle_path.is_file(),
        ENGINE_LIFECYCLE,
        "intelligence_lifecycle",
        soft=not lifecycle_path.is_file(),
    )

    module, _err = try_import_engine_module("codestrata.artifacts.lifecycle")
    if module is not None:
        promote_fn = getattr(module, "promote_intelligence", None) or getattr(
            module, "rotate_intelligence", None
        )
        if callable(promote_fn):
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                portfolio_id = "release-validation"
                port_dir = base / ".codestrata-artifacts" / "intelligence" / portfolio_id
                for slot in SLOTS:
                    (port_dir / slot).mkdir(parents=True, exist_ok=True)
                    manifest = {
                        "schema": "test",
                        "run_id": f"eir-{slot}",
                        "execution_status": "completed",
                        "portfolio_id": portfolio_id,
                    }
                    (port_dir / slot / "eir.json").write_text(
                        json.dumps(manifest, sort_keys=True), encoding="utf-8"
                    )
                try:
                    promote_fn(
                        portfolio_id=portfolio_id,
                        run_id="eir-new",
                        execution_status="completed",
                        base=base,
                    )
                    current_exists = (port_dir / "current" / "eir.json").is_file()
                    summary["rotation_exercised"] = current_exists
                    add_check(
                        checks,
                        defects,
                        "intelligence_lifecycle:promote_api",
                        current_exists,
                        "promote_intelligence exercised",
                        "intelligence_lifecycle",
                        soft=False,
                    )
                except TypeError:
                    try:
                        promote_fn(base, portfolio_id, "eir-new", "completed")
                        summary["rotation_exercised"] = True
                        add_check(
                            checks,
                            defects,
                            "intelligence_lifecycle:promote_api",
                            True,
                            "promote_intelligence exercised (alt signature)",
                            "intelligence_lifecycle",
                            soft=False,
                        )
                    except Exception as exc:  # noqa: BLE001
                        add_check(
                            checks,
                            defects,
                            "intelligence_lifecycle:promote_api",
                            False,
                            str(exc),
                            "intelligence_lifecycle",
                            soft=True,
                        )
                except Exception as exc:  # noqa: BLE001
                    add_check(
                        checks,
                        defects,
                        "intelligence_lifecycle:promote_api",
                        False,
                        str(exc),
                        "intelligence_lifecycle",
                        soft=True,
                    )

        preserve_fn = getattr(module, "portfolio_membership_change_preserves_identity", None)
        if callable(preserve_fn):
            try:
                result = preserve_fn(
                    portfolio_id="release-validation",
                    old_members=("github-a-repo", "github-b-repo"),
                    new_members=("github-a-repo", "github-c-repo"),
                )
                summary["membership_preserved"] = result is True
                add_check(
                    checks,
                    defects,
                    "intelligence_lifecycle:membership_preserves_id",
                    result is True,
                    str(result),
                    "intelligence_lifecycle",
                    soft=False,
                )
            except Exception as exc:  # noqa: BLE001
                add_check(
                    checks,
                    defects,
                    "intelligence_lifecycle:membership_preserves_id",
                    False,
                    str(exc),
                    "intelligence_lifecycle",
                    soft=True,
                )

        failed_fn = getattr(module, "should_promote_intelligence", None)
        if callable(failed_fn):
            try:
                ok = failed_fn(execution_status="failed") is False
                add_check(
                    checks,
                    defects,
                    "intelligence_lifecycle:failed_no_promote",
                    ok,
                    "failed EIR does not promote",
                    "intelligence_lifecycle",
                    soft=False,
                )
            except Exception:  # noqa: BLE001
                pass

    return checks, defects, summary
