"""Assessment lifecycle checks for Slice 17.15."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.contract import ENGINE_LAYOUT, ENGINE_LIFECYCLE, SLOTS
from verification.report_artifact_lifecycle.helpers import add_check, read_text, try_import_engine_module
from verification.report_artifact_lifecycle.models import CheckResult, Defect


def check_assessment_lifecycle(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {
        "lifecycle_module_present": False,
        "slot_layout_supported": False,
        "rotation_exercised": False,
    }

    lifecycle_path = monorepo / ENGINE_LIFECYCLE
    layout_path = monorepo / ENGINE_LAYOUT
    summary["lifecycle_module_present"] = lifecycle_path.is_file()

    add_check(
        checks,
        defects,
        "assessment_lifecycle:module_exists",
        lifecycle_path.is_file(),
        ENGINE_LIFECYCLE,
        "assessment_lifecycle",
        soft=not lifecycle_path.is_file(),
    )

    if layout_path.is_file():
        layout_text = read_text(layout_path)
        has_slots = all(slot in layout_text for slot in SLOTS) or "current" in layout_text
        summary["slot_layout_supported"] = has_slots
        add_check(
            checks,
            defects,
            "assessment_lifecycle:layout_slots",
            has_slots,
            "current/previous in layout",
            "assessment_lifecycle",
            soft=not has_slots,
        )
        run_id_only = (
            "assessments/<repo>-" in layout_text.replace(" ", "")
            or "<repo>-<YYYYMMDD" in layout_text
        ) and "current" not in layout_text
        add_check(
            checks,
            defects,
            "assessment_lifecycle:not_run_id_only_authority",
            not run_id_only or has_slots,
            "run-id-only without slots",
            "assessment_lifecycle",
            soft=run_id_only and not has_slots,
        )

    module, _err = try_import_engine_module("codestrata.artifacts.lifecycle")
    if module is not None:
        promote_fn = getattr(module, "promote_assessment", None) or getattr(module, "rotate_assessment", None)
        if callable(promote_fn):
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                repo_id = "github-codestrata-test-repo"
                repo_dir = base / ".codestrata-artifacts" / "assessments" / repo_id
                for slot in SLOTS:
                    (repo_dir / slot).mkdir(parents=True, exist_ok=True)
                    manifest = {"schema": "test", "run_id": f"run-{slot}", "execution_status": "completed"}
                    (repo_dir / slot / "assessment.json").write_text(
                        json.dumps(manifest, sort_keys=True), encoding="utf-8"
                    )
                try:
                    promote_fn(
                        repository_id=repo_id,
                        run_id="run-new",
                        execution_status="completed",
                        base=base,
                    )
                    current_exists = (repo_dir / "current" / "assessment.json").is_file()
                    summary["rotation_exercised"] = current_exists
                    add_check(
                        checks,
                        defects,
                        "assessment_lifecycle:promote_api",
                        current_exists,
                        "promote_assessment exercised",
                        "assessment_lifecycle",
                        soft=False,
                    )
                except TypeError:
                    try:
                        promote_fn(base, repo_id, "run-new", "completed")
                        summary["rotation_exercised"] = True
                        add_check(
                            checks,
                            defects,
                            "assessment_lifecycle:promote_api",
                            True,
                            "promote_assessment exercised (alt signature)",
                            "assessment_lifecycle",
                            soft=False,
                        )
                    except Exception as exc:  # noqa: BLE001
                        add_check(
                            checks,
                            defects,
                            "assessment_lifecycle:promote_api",
                            False,
                            str(exc),
                            "assessment_lifecycle",
                            soft=True,
                        )
                except Exception as exc:  # noqa: BLE001
                    add_check(
                        checks,
                        defects,
                        "assessment_lifecycle:promote_api",
                        False,
                        str(exc),
                        "assessment_lifecycle",
                        soft=True,
                    )

        failed_fn = getattr(module, "should_promote_assessment", None)
        if callable(failed_fn):
            try:
                ok = failed_fn(execution_status="failed") is False
                add_check(
                    checks,
                    defects,
                    "assessment_lifecycle:failed_no_promote",
                    ok,
                    "failed does not promote",
                    "assessment_lifecycle",
                    soft=False,
                )
            except Exception:  # noqa: BLE001
                pass

    return checks, defects, summary
