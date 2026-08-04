"""Demo artifact digest verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from verification.release_artifacts.contract import DEMO_RELATIVE
from verification.release_artifacts.models import CheckResult, Defect


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def check_demo_artifacts(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    digests: dict[str, str] = {}

    demo_dir = monorepo / DEMO_RELATIVE
    manifest_path = demo_dir / "export-manifest.json"
    if not manifest_path.is_file():
        checks.append(
            CheckResult(
                name="demo_artifacts:manifest_present",
                ok=False,
                detail="missing export-manifest.json",
                category="demo_artifacts",
            )
        )
        return checks, defects, digests

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts") or []
    checks.append(
        CheckResult(
            name="demo_artifacts:manifest_present",
            ok=True,
            detail=f"artifacts={len(artifacts)}",
            category="demo_artifacts",
        )
    )

    for item in artifacts:
        if not isinstance(item, dict):
            continue
        filename = str(item.get("filename") or "")
        expected = str(item.get("sha256") or "")
        if not filename:
            continue
        path = demo_dir / filename
        if not path.is_file():
            defects.append(
                Defect(
                    classification="missing_demo_file",
                    component=filename,
                    expected="present",
                    actual="missing",
                )
            )
            continue
        actual = _sha256(path)
        rel = f"{DEMO_RELATIVE}/{filename}"
        digests[rel] = actual
        checks.append(
            CheckResult(
                name=f"demo_artifacts:digest_{filename}",
                ok=actual == expected,
                detail=f"expected={expected[:16]}… actual={actual[:16]}…",
                category="demo_artifacts",
            )
        )
        if actual != expected:
            defects.append(
                Defect(
                    classification="digest_mismatch",
                    component=filename,
                    expected=expected,
                    actual=actual,
                )
            )

    return checks, defects, digests
