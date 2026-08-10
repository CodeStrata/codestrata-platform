"""Assessment manifest validation for Slice 17.19."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import (
    ASSESSMENT_JSON,
    ASSESSMENT_MANIFEST_SCHEMA,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    artifact_text_is_safe,
    check,
    hard_defect,
    load_json,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)

REQUIRED_FIELDS = (
    "schema",
    "repository_id",
    "assessment_run_id",
    "artifact_slot",
    "completed_heads",
)


def check_assessment_manifests(
    monorepo: Path,
    selection: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    per_repo: list[dict[str, Any]] = []

    for item in selection.get("selected") or []:
        catalog_id = str(item.get("catalog_id") or "")
        rel = item.get("current_relative")
        if not rel:
            continue
        current = monorepo / str(rel)
        path = current / ASSESSMENT_JSON
        if not path.is_file():
            checks.append(
                check(
                    f"manifest:exists:{catalog_id}",
                    False,
                    "missing",
                    "assessment_manifest",
                )
            )
            defects.append(
                hard_defect(
                    "missing_manifest",
                    f"manifest:exists:{catalog_id}",
                    "present",
                    "absent",
                )
            )
            continue

        manifest = load_json(path)
        text = read_text(path)
        size = path.stat().st_size
        heads_dir = current / "heads"
        heads_size = 0
        if heads_dir.is_dir():
            for hp in heads_dir.glob("*.json"):
                heads_size += hp.stat().st_size

        schema_ok = manifest.get("schema") == ASSESSMENT_MANIFEST_SCHEMA
        checks.append(
            check(
                f"manifest:schema:{catalog_id}",
                schema_ok,
                str(manifest.get("schema")),
                "assessment_manifest",
            )
        )
        if not schema_ok:
            defects.append(
                hard_defect(
                    "manifest_schema",
                    f"manifest:schema:{catalog_id}",
                    ASSESSMENT_MANIFEST_SCHEMA,
                    str(manifest.get("schema")),
                )
            )

        slot_ok = manifest.get("artifact_slot") == "current"
        checks.append(
            check(
                f"manifest:artifact_slot:{catalog_id}",
                slot_ok,
                str(manifest.get("artifact_slot")),
                "assessment_manifest",
            )
        )
        if not slot_ok:
            defects.append(
                hard_defect(
                    "artifact_slot",
                    f"manifest:artifact_slot:{catalog_id}",
                    "current",
                    str(manifest.get("artifact_slot")),
                )
            )

        missing_fields = [f for f in REQUIRED_FIELDS if f not in manifest]
        fields_ok = not missing_fields
        checks.append(
            check(
                f"manifest:required_fields:{catalog_id}",
                fields_ok,
                ",".join(missing_fields) if missing_fields else "ok",
                "assessment_manifest",
            )
        )
        if not fields_ok:
            defects.append(
                hard_defect(
                    "manifest_fields",
                    f"manifest:required_fields:{catalog_id}",
                    "present",
                    ",".join(missing_fields),
                )
            )

        # Lightweight: completed_heads are refs only; file much smaller than heads sum.
        completed = manifest.get("completed_heads") or []
        embeds_payload = False
        if isinstance(completed, list):
            for ref in completed:
                if isinstance(ref, dict) and (
                    "findings" in ref or "scores" in ref or "evidence" in ref
                ):
                    embeds_payload = True
        # Also reject huge manifests relative to head payloads.
        lightweight = (not embeds_payload) and (
            heads_size == 0 or size < max(8_000, heads_size // 2)
        )
        checks.append(
            check(
                f"manifest:lightweight:{catalog_id}",
                lightweight,
                f"bytes={size};heads_bytes={heads_size};embeds={embeds_payload}",
                "assessment_manifest",
            )
        )
        if not lightweight:
            defects.append(
                hard_defect(
                    "manifest_not_lightweight",
                    f"manifest:lightweight:{catalog_id}",
                    "lightweight",
                    f"bytes={size}",
                )
            )

        safe = artifact_text_is_safe(text)
        checks.append(
            check(
                f"manifest:privacy:{catalog_id}",
                safe,
                "no absolute paths/credentials",
                "assessment_manifest",
            )
        )
        if not safe:
            defects.append(
                hard_defect(
                    "manifest_privacy",
                    f"manifest:privacy:{catalog_id}",
                    "safe",
                    "forbidden pattern",
                )
            )

        per_repo.append(
            {
                "catalog_id": catalog_id,
                "schema": manifest.get("schema"),
                "artifact_slot": manifest.get("artifact_slot"),
                "assessment_run_id": manifest.get("assessment_run_id"),
                "repository_id": manifest.get("repository_id"),
                "completed_heads_count": len(completed) if isinstance(completed, list) else 0,
                "manifest_bytes": size,
                "heads_bytes": heads_size,
                "lightweight": lightweight,
            }
        )

    summary = {
        "repositories": per_repo,
        "all_lightweight": all(r.get("lightweight") for r in per_repo) if per_repo else False,
    }
    return checks, defects, summary
