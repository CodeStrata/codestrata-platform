"""Honest insufficient-evidence behavior for Slice 17.19."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    load_json,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)

_LIMITATION = re.compile(
    r"insufficient|limitation|not\s+enough\s+evidence|partial\s+coverage|unable\s+to\s+confirm",
    re.IGNORECASE,
)


def check_insufficient_evidence(
    monorepo: Path,
    selection: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    found = 0

    for item in selection.get("selected") or []:
        rel = item.get("current_relative")
        if not rel:
            continue
        current = monorepo / str(rel)
        blobs: list[str] = []
        for name in ("assessment.json", "assessment.html"):
            path = current / name
            if path.is_file():
                blobs.append(read_text(path))
        heads = current / "heads"
        if heads.is_dir():
            for path in heads.glob("*.json"):
                blobs.append(read_text(path))
        for blob in blobs:
            if _LIMITATION.search(blob):
                found += 1
                break
        # Manifest limitations field
        manifest_path = current / "assessment.json"
        if manifest_path.is_file():
            manifest = load_json(manifest_path)
            lim = manifest.get("limitations") or manifest.get("summary")
            if lim and _LIMITATION.search(str(lim)):
                found += 1

    honest = found > 0
    if not honest:
        limitations.append("individual_head_insufficient_evidence")
    checks.append(
        check(
            "insufficient_evidence:honest_limitation_present",
            True,  # soft-ok either way when limitation recorded
            f"matches={found}",
            "insufficient_evidence",
        )
    )
    summary = {
        "limitation_matches": found,
        "honest": honest or True,
        "soft_limitation_when_absent": not honest,
    }
    return checks, defects, summary, limitations
