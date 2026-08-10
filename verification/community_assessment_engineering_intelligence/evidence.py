"""Evidence traceability checks for Slice 17.19."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    load_json,
    load_json_any,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def _iter_findings(current: Path) -> list[dict[str, Any]]:
    findings_path = current / "findings.json"
    findings: list[dict[str, Any]] = []
    if findings_path.is_file():
        raw = load_json_any(findings_path)
        if isinstance(raw, dict):
            items = raw.get("findings") or raw.get("items") or []
            if isinstance(items, list):
                findings.extend(x for x in items if isinstance(x, dict))
        elif isinstance(raw, list):
            findings.extend(x for x in raw if isinstance(x, dict))
    heads = current / "heads"
    if heads.is_dir():
        for path in heads.glob("*.json"):
            try:
                payload = load_json_any(path)
            except (OSError, json.JSONDecodeError, TypeError):
                continue
            if not isinstance(payload, dict):
                continue
            items = payload.get("findings") or []
            if isinstance(items, list):
                findings.extend(x for x in items if isinstance(x, dict))
    return findings


def _path_looks_absolute(value: str) -> bool:
    return value.startswith("/Users/") or value.startswith("/home/") or (
        len(value) > 2 and value[1] == ":" and value[0].isalpha()
    )


def check_evidence(
    monorepo: Path,
    selection: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    broken = 0
    sampled = 0
    absolute = 0

    for item in selection.get("selected") or []:
        catalog_id = str(item.get("catalog_id") or "")
        rel = item.get("current_relative")
        if not rel:
            continue
        current = monorepo / str(rel)
        findings = _iter_findings(current)
        sample = findings[:25]
        sampled += len(sample)
        repo_broken = 0
        for finding in sample:
            refs: list[str] = []
            primary = finding.get("primary_evidence_id")
            if isinstance(primary, str):
                refs.append(primary)
            for ref in finding.get("evidence_refs") or []:
                if isinstance(ref, dict):
                    for key in ("evidence_id", "id", "path", "file_path", "relative_path"):
                        val = ref.get(key)
                        if isinstance(val, str) and val.strip():
                            refs.append(val.strip())
                elif isinstance(ref, str):
                    refs.append(ref)
            for key in ("path", "file_path", "relative_path", "source_path"):
                val = finding.get(key)
                if isinstance(val, str) and val.strip():
                    refs.append(val.strip())
            for ref in refs:
                if _path_looks_absolute(ref):
                    absolute += 1
                    repo_broken += 1
                # Empty evidence id with claim is broken.
                if ref.strip() == "":
                    repo_broken += 1
        broken += repo_broken
        ok = repo_broken == 0
        checks.append(
            check(
                f"evidence:repo_relative:{catalog_id}",
                ok,
                f"sampled={len(sample)};broken={repo_broken}",
                "evidence",
            )
        )
        if not ok:
            defects.append(
                hard_defect(
                    "broken_evidence_ref",
                    f"evidence:repo_relative:{catalog_id}",
                    "repo-relative",
                    f"broken={repo_broken}",
                )
            )

        # Manifest presence of findings_summary is fine without findings file.
        manifest_path = current / "assessment.json"
        if manifest_path.is_file():
            manifest = load_json(manifest_path)
            _ = manifest.get("findings_summary")

    summary = {
        "sampled_findings": sampled,
        "broken_refs": broken,
        "absolute_paths": absolute,
        "ok": broken == 0,
    }
    return checks, defects, summary
