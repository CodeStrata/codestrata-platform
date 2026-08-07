"""Manifest, inventory, and checksum validation."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from verification.infrastructure_repository_export.contract import (
    ARTIFACT_FILENAMES,
    MANIFEST_SCHEMA_NAME,
    MANIFEST_SCHEMA_VERSION,
    REPOSITORY_NAME,
    TARGET,
    VALIDATION_ROOTS,
)
from verification.infrastructure_repository_export.dual_export import (
    _iter_files,
    mode_category,
    sha256_file,
)
from verification.infrastructure_repository_export.models import CheckResult, Defect

_ABS = re.compile(r"(?<![\w.-])(/Users/|/home/|file://|[A-Za-z]:\\\\Users\\\\)")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = export_root / "export-manifest.json"
    if not path.is_file():
        return (
            [CheckResult("manifest:present", False, "missing", "manifest")],
            [Defect("manifest/inventory/checksum defect", "manifest", "present", "missing")],
        )
    data = _load_json(path)
    blob = json.dumps(data, sort_keys=True)
    checks.extend(
        [
            CheckResult(
                "manifest:schema",
                data.get("schema_name") == MANIFEST_SCHEMA_NAME
                and data.get("schema_version") == MANIFEST_SCHEMA_VERSION,
                f"{data.get('schema_name')}:{data.get('schema_version')}",
                "manifest",
            ),
            CheckResult(
                "manifest:target_name",
                data.get("target") == TARGET
                and data.get("repository_name") == REPOSITORY_NAME,
                REPOSITORY_NAME,
                "manifest",
            ),
            CheckResult(
                "manifest:no_abs_path",
                not _ABS.search(blob),
                "no absolute paths",
                "manifest",
            ),
            CheckResult(
                "manifest:no_timestamp",
                "timestamp" not in blob.lower() and "created_at" not in blob,
                "no timestamps",
                "manifest",
            ),
            CheckResult(
                "manifest:validation_roots",
                tuple(data.get("validation_roots") or ()) == VALIDATION_ROOTS,
                "roots exact",
                "manifest",
            ),
        ]
    )

    files = data.get("files") or []
    paths = [f["path"] for f in files]
    checks.append(
        CheckResult(
            "manifest:sorted_paths",
            paths == sorted(paths),
            f"count={len(paths)}",
            "manifest",
        )
    )
    checks.append(
        CheckResult(
            "manifest:no_duplicates",
            len(paths) == len(set(paths)),
            "unique paths",
            "manifest",
        )
    )
    checks.append(
        CheckResult(
            "manifest:file_count",
            data.get("file_count") == len(files),
            str(data.get("file_count")),
            "manifest",
        )
    )
    checks.append(
        CheckResult(
            "manifest:no_self_in_files",
            not any(p in ARTIFACT_FILENAMES for p in paths),
            "artifacts excluded from managed file list",
            "manifest",
        )
    )

    # Independent checksum recalculation
    checksums = data.get("checksums") or {}
    mismatch = []
    for rel, expected in sorted(checksums.items()):
        file_path = export_root / rel
        if not file_path.is_file():
            mismatch.append(rel)
            continue
        if sha256_file(file_path) != expected:
            mismatch.append(rel)
    checks.append(
        CheckResult(
            "manifest:checksums_independent",
            not mismatch,
            "ok" if not mismatch else f"mismatch_count={len(mismatch)}",
            "checksum",
        )
    )

    # Case collisions
    lower = {}
    case_ok = True
    for p in paths:
        key = p.lower()
        if key in lower and lower[key] != p:
            case_ok = False
            break
        lower[key] = p
    checks.append(CheckResult("manifest:no_case_collision", case_ok, "case", "manifest"))

    # Traversal
    trav_ok = all(".." not in p.split("/") and not p.startswith("/") for p in paths)
    checks.append(CheckResult("manifest:no_traversal", trav_ok, "relative", "manifest"))

    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "manifest/inventory/checksum defect",
                "manifest",
                "valid",
                "invalid",
            )
        )
    return checks, defects


def validate_inventory(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = export_root / "export-inventory.json"
    data = _load_json(path)
    records = data.get("files") or []
    paths = [r["path"] for r in records]
    checks.append(
        CheckResult(
            "inventory:sorted",
            paths == sorted(paths),
            f"count={len(paths)}",
            "inventory",
        )
    )
    forbidden_fields = {"owner", "inode", "mtime", "source_absolute", "destination_absolute"}
    field_ok = True
    for rec in records:
        if forbidden_fields & set(rec.keys()):
            field_ok = False
            break
        for key in ("path", "source_classification", "mode", "sha256", "size"):
            if key not in rec:
                field_ok = False
                break
    checks.append(CheckResult("inventory:fields", field_ok, "required fields only", "inventory"))

    mismatch = 0
    for rec in records:
        fp = export_root / rec["path"]
        if not fp.is_file():
            mismatch += 1
            continue
        if sha256_file(fp) != rec["sha256"]:
            mismatch += 1
            continue
        if fp.stat().st_size != rec["size"]:
            mismatch += 1
            continue
        if mode_category(fp) != rec["mode"]:
            mismatch += 1
    checks.append(
        CheckResult(
            "inventory:matches_bytes",
            mismatch == 0,
            "ok" if mismatch == 0 else f"mismatch={mismatch}",
            "inventory",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "manifest/inventory/checksum defect",
                "inventory",
                "valid",
                "invalid",
            )
        )
    return checks, defects


def validate_checksums(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    sums_path = export_root / "SHA256SUMS"
    lines = [
        line.strip()
        for line in sums_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    parsed: dict[str, str] = {}
    abs_ok = True
    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        digest, rel = parts[0], parts[-1]
        if rel.startswith("/") or ".." in rel.split("/") or "\\" in rel:
            abs_ok = False
        parsed[rel] = digest

    checks.append(
        CheckResult(
            "checksums:sorted",
            list(parsed) == sorted(parsed),
            f"lines={len(parsed)}",
            "checksum",
        )
    )
    checks.append(CheckResult("checksums:relative_only", abs_ok, "forward-slash relative", "checksum"))
    checks.append(
        CheckResult(
            "checksums:no_self",
            "SHA256SUMS" not in parsed and "export-manifest.json" not in parsed,
            "self-ref excluded",
            "checksum",
        )
    )

    # Independent coverage of managed files (non-artifacts)
    tree = _iter_files(export_root)
    managed = {p for p in tree if p not in ARTIFACT_FILENAMES}
    missing = sorted(managed - set(parsed))
    unknown = sorted(set(parsed) - managed)
    checks.append(
        CheckResult(
            "checksums:coverage",
            not missing and not unknown,
            f"missing={len(missing)} unknown={len(unknown)}",
            "checksum",
        )
    )
    bad = 0
    for rel, expected in parsed.items():
        if sha256_file(export_root / rel) != expected:
            bad += 1
    checks.append(
        CheckResult(
            "checksums:independent_match",
            bad == 0,
            "ok" if bad == 0 else f"bad={bad}",
            "checksum",
        )
    )

    # Cross-agree with manifest
    manifest = _load_json(export_root / "export-manifest.json")
    msums = manifest.get("checksums") or {}
    checks.append(
        CheckResult(
            "checksums:agree_manifest",
            msums == parsed,
            "manifest checksums == SHA256SUMS",
            "checksum",
        )
    )

    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "manifest/inventory/checksum defect",
                "checksums",
                "valid",
                "invalid",
            )
        )
    return checks, defects
