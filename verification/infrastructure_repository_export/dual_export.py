"""Dual export + tree comparison helpers."""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from verification.infrastructure_repository_export.models import CheckResult, Defect

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from repository_export.exporter import export_infrastructure_repository  # noqa: E402


@dataclass
class ExportTrees:
    parent: Path
    export_a: Path
    export_b: Path
    validation_copy: Path | None = None
    dry_run_touched: bool = False
    diagnostics: dict = field(default_factory=dict)


def _iter_files(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        # Skip validation artifacts if any
        dirnames[:] = sorted(
            n
            for n in dirnames
            if n
            not in {
                ".terraform",
                ".tofu",
                "__pycache__",
                ".pytest_cache",
                ".venv",
            }
        )
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if path.is_symlink():
                continue
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            files[rel] = path
    return files


def mode_category(path: Path) -> str:
    mode = path.stat().st_mode & 0o777
    return "executable" if mode & 0o111 else "regular"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_trees(a: Path, b: Path) -> tuple[list[CheckResult], list[Defect]]:
    files_a = _iter_files(a)
    files_b = _iter_files(b)
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    set_a = set(files_a)
    set_b = set(files_b)
    checks.append(
        CheckResult(
            "tree:same_file_set",
            set_a == set_b,
            f"count_a={len(set_a)} count_b={len(set_b)}",
            "determinism",
        )
    )
    if set_a != set_b:
        defects.append(
            Defect(
                "determinism defect",
                "tree_set",
                "identical relative paths",
                f"only_a={len(set_a - set_b)} only_b={len(set_b - set_a)}",
            )
        )

    byte_ok = True
    mode_ok = True
    for rel in sorted(set_a & set_b):
        if files_a[rel].read_bytes() != files_b[rel].read_bytes():
            byte_ok = False
            break
        if mode_category(files_a[rel]) != mode_category(files_b[rel]):
            mode_ok = False
            break
    checks.append(CheckResult("tree:byte_identical", byte_ok, "all files", "determinism"))
    checks.append(CheckResult("tree:mode_identical", mode_ok, "mode categories", "determinism"))
    if not byte_ok:
        defects.append(
            Defect("determinism defect", "tree_bytes", "identical", "mismatch")
        )
    if not mode_ok:
        defects.append(
            Defect("determinism defect", "tree_modes", "identical", "mismatch")
        )

    for name in ("export-manifest.json", "export-inventory.json", "SHA256SUMS"):
        pa = a / name
        pb = b / name
        ok = pa.is_file() and pb.is_file() and pa.read_bytes() == pb.read_bytes()
        checks.append(
            CheckResult(f"tree:artifact_{name.replace('.', '_')}", ok, name, "determinism")
        )
        if not ok:
            defects.append(
                Defect("determinism defect", name, "identical artifact bytes", "mismatch")
            )
    return checks, defects


def perform_dual_export(monorepo: Path) -> tuple[ExportTrees, list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    parent = Path(tempfile.mkdtemp(prefix="sv127-infra-export-"))
    export_a = parent / "export-a"
    export_b = parent / "export-b"
    dry_dest = parent / "dry-run-dest"

    # Dry-run first
    dry = export_infrastructure_repository(
        destination=dry_dest, dry_run=True, source_root=monorepo
    )
    dry_ok = dry.diagnostics.status == "ok" and not dry_dest.exists()
    checks.append(
        CheckResult("export:dry_run_ok", dry_ok, "dry-run no write", "exporter")
    )
    if not dry_ok:
        defects.append(
            Defect("exporter defect", "dry_run", "no destination write", "wrote_or_failed")
        )

    r_a = export_infrastructure_repository(
        destination=export_a, dry_run=False, source_root=monorepo
    )
    r_b = export_infrastructure_repository(
        destination=export_b, dry_run=False, source_root=monorepo
    )
    export_ok = (
        r_a.diagnostics.status == "ok"
        and r_b.diagnostics.status == "ok"
        and export_a.is_dir()
        and export_b.is_dir()
    )
    checks.append(CheckResult("export:dual_ok", export_ok, "two exports", "exporter"))
    if not export_ok:
        defects.append(Defect("exporter defect", "dual_export", "ok", "failed"))

    trees = ExportTrees(
        parent=parent,
        export_a=export_a,
        export_b=export_b,
        diagnostics={
            "file_count": r_a.diagnostics.file_count,
            "executable_file_count": r_a.diagnostics.executable_file_count,
            "generated_file_count": r_a.diagnostics.generated_file_count,
        },
    )
    return trees, checks, defects


def make_validation_copy(export_a: Path) -> Path:
    parent = export_a.parent
    dest = parent / "validation-copy"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(export_a, dest, symlinks=False)
    return dest


def cleanup_trees(trees: ExportTrees) -> None:
    shutil.rmtree(trees.parent, ignore_errors=True)
