"""Assessment head discovery and validation for Slice 17.19."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import HEADS_PY
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    load_json,
    load_json_any,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)

_INSUFFICIENT = re.compile(
    r"insufficient[_\s-]?evidence|not[_\s-]?enough[_\s-]?evidence|limited[_\s-]?evidence",
    re.IGNORECASE,
)
_NOT_APPLICABLE = re.compile(r"not[_\s-]?applicable|n/?a\b", re.IGNORECASE)
_NOT_SUPPORTED = re.compile(
    r"not[_\s-]?supported|unsupported|technology[_\s-]?not[_\s-]supported",
    re.IGNORECASE,
)


def discover_head_specs(monorepo: Path) -> list[dict[str, str]]:
    path = monorepo / HEADS_PY
    if not path.is_file():
        return []
    tree = ast.parse(read_text(path))
    specs: list[dict[str, str]] = []
    for node in tree.body:
        target_name: str | None = None
        value_node = None
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    target_name = target.id
                    value_node = node.value
                    break
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
            value_node = node.value
        if target_name != "ASSESSMENT_HEAD_SPECS" or not isinstance(value_node, ast.Tuple):
            continue
        for elt in value_node.elts:
            if not isinstance(elt, ast.Call):
                continue
            kwargs: dict[str, str] = {}
            for kw in elt.keywords:
                if kw.arg and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    kwargs[kw.arg] = kw.value.value
            # Positional AssessmentHeadSpec(head_id, heads_basename, legacy_filename)
            pos: list[str] = []
            for arg in elt.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    pos.append(arg.value)
            if "head_id" not in kwargs and len(pos) >= 1:
                kwargs["head_id"] = pos[0]
            if "heads_basename" not in kwargs and len(pos) >= 2:
                kwargs["heads_basename"] = pos[1]
            if "legacy_filename" not in kwargs and len(pos) >= 3:
                kwargs["legacy_filename"] = pos[2]
            if "head_id" in kwargs and "heads_basename" in kwargs:
                specs.append(
                    {
                        "head_id": kwargs["head_id"],
                        "heads_basename": kwargs["heads_basename"],
                        "legacy_filename": kwargs.get("legacy_filename", ""),
                    }
                )
    return specs


def _classify_missing(head_payload: Any | None, *, present: bool) -> str:
    if present:
        return "present"
    if head_payload is None:
        return "not_generated"
    blob = json.dumps(head_payload, sort_keys=True) if not isinstance(head_payload, str) else head_payload
    if _NOT_SUPPORTED.search(blob):
        return "NOT_SUPPORTED"
    if _NOT_APPLICABLE.search(blob):
        return "NOT_APPLICABLE"
    if _INSUFFICIENT.search(blob):
        return "INSUFFICIENT_EVIDENCE"
    return "not_generated"


def check_heads(
    monorepo: Path,
    selection: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    specs = discover_head_specs(monorepo)
    checks.append(
        check(
            "heads:specs_discovered",
            len(specs) > 0,
            f"count={len(specs)}",
            "heads",
        )
    )
    if not specs:
        defects.append(
            hard_defect("heads_specs", "heads:specs_discovered", ">0", "0")
        )

    per_repo: list[dict[str, Any]] = []
    for item in selection.get("selected") or []:
        catalog_id = str(item.get("catalog_id") or "")
        rel = item.get("current_relative")
        if not rel:
            continue
        current = monorepo / str(rel)
        heads_dir = current / "heads"
        present_files = {
            p.name: p for p in heads_dir.glob("*.json")
        } if heads_dir.is_dir() else {}

        head_rows: list[dict[str, Any]] = []
        for spec in specs:
            basename = spec["heads_basename"]
            path = present_files.get(basename)
            present = path is not None and path.is_file()
            payload: Any | None = None
            if present and path is not None:
                try:
                    payload = load_json_any(path)
                except (OSError, json.JSONDecodeError, TypeError):
                    payload = None
                    present = False
            status = _classify_missing(payload, present=present)
            if status == "present":
                ok_obj = isinstance(payload, dict)
                checks.append(
                    check(
                        f"heads:object:{catalog_id}:{spec['head_id']}",
                        ok_obj,
                        "object" if ok_obj else type(payload).__name__,
                        "heads",
                    )
                )
                if not ok_obj:
                    defects.append(
                        hard_defect(
                            "head_not_object",
                            f"heads:object:{catalog_id}:{spec['head_id']}",
                            "object",
                            type(payload).__name__,
                        )
                    )
                # Soft contradiction heuristic: empty findings_summary with huge findings.
                if isinstance(payload, dict):
                    schemaish = any(
                        k in payload
                        for k in ("schema", "schema_version", "head_id", "findings", "scores", "status")
                    )
                    checks.append(
                        check(
                            f"heads:schemaish:{catalog_id}:{spec['head_id']}",
                            schemaish,
                            "keys present" if schemaish else "minimal",
                            "heads",
                        )
                    )
            else:
                if status == "INSUFFICIENT_EVIDENCE":
                    limitations.append("individual_head_insufficient_evidence")
                elif status == "NOT_SUPPORTED":
                    limitations.append("unsupported_head_for_technology")
                elif status == "not_generated" and spec["head_id"] == "ai":
                    limitations.append("ai_narrative_not_requested")
                elif status in {"NOT_APPLICABLE", "not_generated"}:
                    limitations.append("individual_head_insufficient_evidence")
                checks.append(
                    check(
                        f"heads:missing_classified:{catalog_id}:{spec['head_id']}",
                        True,
                        status,
                        "heads",
                    )
                )
            head_rows.append(
                {
                    "head_id": spec["head_id"],
                    "basename": basename,
                    "status": status,
                }
            )

        per_repo.append(
            {
                "catalog_id": catalog_id,
                "present_count": sum(1 for h in head_rows if h["status"] == "present"),
                "heads": head_rows,
            }
        )

    summary = {
        "spec_count": len(specs),
        "specs": specs,
        "repositories": per_repo,
    }
    return checks, defects, summary, sorted(set(limitations))
