"""Suite manifest validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.contract import MANIFEST_JSON, SV1713_OUTPUT_RELATIVE
from verification.community_22_repository_validation.determinism import report_text_is_safe
from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect


def check_manifest(monorepo: Path, manifest: dict[str, Any]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    text = json.dumps(manifest, sort_keys=True)
    add_check(
        checks,
        defects,
        "manifest:safe_text",
        report_text_is_safe(text),
        "no secrets or absolute paths",
        "manifest",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "manifest:repository_list",
        isinstance(manifest.get("repositories"), list),
        str(len(manifest.get("repositories") or [])),
        "manifest",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    expected = f"{SV1713_OUTPUT_RELATIVE}/{MANIFEST_JSON}"
    add_check(
        checks,
        defects,
        "manifest:relative_path",
        expected.startswith(".codestrata-artifacts/"),
        expected,
        "manifest",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects
