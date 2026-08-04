"""Load preserved inputs for SV.15 (no full 22-repo reassessment)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.deterministic_outputs.contract import (
    DETERMINISM_SAMPLE_IDS,
    SV10_DETERMINISM_SAMPLES,
    SV10_OUTPUT_RELATIVE,
    SV12_OUTPUT_RELATIVE,
    TARGET_REPOSITORY_COUNT,
)
from verification.engineering_intelligence.catalog import monorepo_root_from_here


class Sv15InputError(RuntimeError):
    """Raised when required preserved inputs are missing."""


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_sv10_determinism_samples(monorepo: Path | None = None) -> list[dict[str, Any]]:
    root = (monorepo or monorepo_root_from_here()).resolve()
    path = root / SV10_DETERMINISM_SAMPLES
    if not path.is_file():
        raise Sv15InputError(f"missing {SV10_DETERMINISM_SAMPLES}")
    data = _read_json(path)
    if not isinstance(data, list):
        raise Sv15InputError("determinism-samples.json must be a list")
    return data


def load_sample_report(
    repository_id: str,
    monorepo: Path | None = None,
) -> dict[str, Any]:
    root = (monorepo or monorepo_root_from_here()).resolve()
    base = root / SV10_OUTPUT_RELATIVE / "artifacts" / repository_id
    matches = sorted(base.glob("*/report.json"))
    if not matches:
        raise Sv15InputError(f"missing SV.10 report for {repository_id}")
    return _read_json(matches[0])


def load_sample_artifact_bundle(
    repository_id: str,
    monorepo: Path | None = None,
) -> dict[str, Any]:
    root = (monorepo or monorepo_root_from_here()).resolve()
    base = root / SV10_OUTPUT_RELATIVE / "artifacts" / repository_id
    matches = sorted(base.glob("*/report.json"))
    if not matches:
        raise Sv15InputError(f"missing SV.10 artifacts for {repository_id}")
    run_dir = matches[0].parent
    out: dict[str, Any] = {"report": _read_json(run_dir / "report.json")}
    for name in ("findings.json", "recommendations.json"):
        path = run_dir / name
        if path.is_file():
            out[name.replace(".json", "")] = _read_json(path)
    html = run_dir / "report.html"
    if html.is_file():
        out["html"] = html.read_text(encoding="utf-8", errors="replace")
    return out


def sample_repository_ids() -> tuple[str, ...]:
    return DETERMINISM_SAMPLE_IDS


def load_sv12_export_bytes(monorepo: Path | None = None) -> dict[str, bytes]:
    root = (monorepo or monorepo_root_from_here()).resolve()
    base = root / SV12_OUTPUT_RELATIVE
    return {
        "json": (base / "engineering-intelligence-report.json").read_bytes(),
        "html": (base / "engineering-intelligence-report.html").read_bytes(),
        "manifest": (base / "export-manifest.json").read_bytes(),
    }


def verification_report_paths(monorepo: Path) -> list[Path]:
    candidates = [
        monorepo / "engine/reports/verification/sv10/curated-repository-validation.json",
        monorepo
        / "engine/reports/verification/sv11/assessment-consistency-verification.json",
        monorepo
        / "platform/reports/verification/sv12/engineering-intelligence-quality-review.json",
        monorepo
        / "platform/reports/verification/sv13/system-defect-fixes-verification.json",
        monorepo
        / "platform/reports/verification/sv14/cross-schema-compatibility-verification.json",
    ]
    return [p for p in candidates if p.is_file()]


def assert_catalog_count(monorepo: Path | None = None) -> int:
    root = (monorepo or monorepo_root_from_here()).resolve()
    catalog = _read_json(root / "validation/repository-catalog/catalog.json")
    count = sum(
        1
        for item in catalog.get("repositories") or []
        if (item.get("enabled_for") or {}).get("release_validation")
    )
    if count != TARGET_REPOSITORY_COUNT:
        raise Sv15InputError(f"catalog release_validation count {count}")
    return count
