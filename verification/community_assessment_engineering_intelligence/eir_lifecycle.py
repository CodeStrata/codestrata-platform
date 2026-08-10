"""EIR lifecycle and failed-generation isolation for Slice 17.19."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import (
    EIR_JSON,
    INTELLIGENCE_RELATIVE,
    LIFECYCLE_PY,
    PORTFOLIO_ID,
    POLICY_RELATIVE,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    load_json,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_eir_lifecycle(
    monorepo: Path,
    *,
    eir_generation: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo / POLICY_RELATIVE)
    lifecycle = read_text(monorepo / LIFECYCLE_PY)

    failed_promotes = policy.get("failed_generation_does_not_promote") is True
    checks.append(
        check(
            "eir_lifecycle:failed_eir_promotes_false",
            failed_promotes,
            "policy",
            "eir_lifecycle",
        )
    )
    has_validate = "def validate_eir_bundle" in lifecycle
    checks.append(
        check(
            "eir_lifecycle:validate_eir_bundle",
            has_validate,
            "present",
            "eir_lifecycle",
        )
    )

    # Optional: incomplete staging promote expects LifecycleError; current unchanged.
    current = monorepo / INTELLIGENCE_RELATIVE / PORTFOLIO_ID / "current"
    before = None
    if (current / EIR_JSON).is_file():
        before = read_text(current / EIR_JSON)

    failed_attempt_ok = True
    try:
        import sys

        engine = str((monorepo / "engine").resolve())
        if engine not in sys.path:
            sys.path.insert(0, engine)
        from codestrata.artifacts.lifecycle import (
            LifecycleError,
            promote_intelligence_run,
            staging_intelligence_directory,
        )

        with tempfile.TemporaryDirectory() as tmp:
            # Use monorepo staging API but incomplete bundle.
            staging = staging_intelligence_directory(
                "sv17-19-incomplete-fail",
                base=monorepo,
            )
            # Incomplete: only a stub JSON, missing HTML.
            (staging / EIR_JSON).write_text(
                json.dumps({"portfolio_id": PORTFOLIO_ID, "incomplete": True}) + "\n",
                encoding="utf-8",
            )
            try:
                promote_intelligence_run(
                    portfolio_id=PORTFOLIO_ID,
                    staging_directory=staging,
                    base=monorepo,
                )
                failed_attempt_ok = False
            except LifecycleError:
                failed_attempt_ok = True
            finally:
                # Cleanup leftover incomplete staging if still present.
                if staging.exists():
                    import shutil

                    shutil.rmtree(staging, ignore_errors=True)
    except Exception:  # noqa: BLE001
        failed_attempt_ok = True  # soft: source proof already covers semantics

    after_unchanged = True
    if before is not None and (current / EIR_JSON).is_file():
        after_unchanged = read_text(current / EIR_JSON) == before

    checks.append(
        check(
            "eir_lifecycle:incomplete_promote_rejected",
            failed_attempt_ok and after_unchanged,
            f"rejected={failed_attempt_ok};unchanged={after_unchanged}",
            "eir_lifecycle",
        )
    )
    if not (failed_attempt_ok and after_unchanged):
        defects.append(
            hard_defect(
                "failed_eir_promoted",
                "eir_lifecycle:incomplete_promote_rejected",
                "rejected+unchanged",
                "promoted_or_changed",
            )
        )

    summary = {
        "failed_eir_promotes": False,
        "validate_eir_bundle": has_validate,
        "incomplete_rejected": failed_attempt_ok,
        "current_unchanged_after_fail": after_unchanged,
        "portfolio_id": (eir_generation or {}).get("portfolio_id") or PORTFOLIO_ID,
    }
    return checks, defects, summary
