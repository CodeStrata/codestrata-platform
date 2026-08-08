"""Export determinism dual-run checks."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

from verification.repository_package_release_validation.export_validation import _export
from verification.repository_package_release_validation.helpers import (
    add_check,
    inventory_fingerprint,
    rel_paths,
)
from verification.repository_package_release_validation.models import CheckResult, Defect


def check_export_determinism(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict = {}

    with tempfile.TemporaryDirectory(prefix="sv169-det-") as tmp:
        base = Path(tmp)
        for target in ("infrastructure", "insights"):
            a = base / f"{target}-a"
            b = base / f"{target}-b"
            try:
                _export(monorepo, target, a, dry_run=False)
                _export(monorepo, target, b, dry_run=False)
                fa = inventory_fingerprint(rel_paths(a))
                fb = inventory_fingerprint(rel_paths(b))
                identical_inv = fa == fb
                add_check(
                    checks,
                    defects,
                    f"determinism:inventory:{target}",
                    identical_inv,
                    "byte_identical_inventory" if identical_inv else "mismatch",
                    "determinism",
                )
                # compare key files if present
                key_files = []
                if target == "infrastructure":
                    key_files = ["export-manifest.json", "export-inventory.json", "SHA256SUMS", "README.md", "LICENSE"]
                elif target == "insights":
                    key_files = ["package.json", "README.md"]
                file_ok = True
                for name in key_files:
                    pa, pb = a / name, b / name
                    if pa.is_file() and pb.is_file():
                        if pa.read_bytes() != pb.read_bytes():
                            file_ok = False
                    elif pa.exists() != pb.exists():
                        file_ok = False
                add_check(
                    checks,
                    defects,
                    f"determinism:key_files:{target}",
                    file_ok,
                    "identical" if file_ok else "differ",
                    "determinism",
                )
                # no timestamps / absolute paths in inventory-like files
                leak = False
                for p in a.rglob("*"):
                    if not p.is_file() or p.suffix.lower() not in {".json", ".md", ".txt"}:
                        continue
                    text = p.read_text(encoding="utf-8", errors="ignore").lower()
                    if "/users/" in text or "/home/" in text:
                        leak = True
                        break
                    if '"timestamp"' in text:
                        leak = True
                        break
                add_check(
                    checks,
                    defects,
                    f"determinism:no_path_timestamp_leak:{target}",
                    not leak,
                    "safe" if not leak else "leak",
                    "determinism",
                )
                summary[target] = {
                    "inventory_hash": hashlib.sha256(fa.encode()).hexdigest()[:16],
                    "identical": identical_inv and file_ok,
                }
            except Exception as exc:  # noqa: BLE001
                add_check(
                    checks,
                    defects,
                    f"determinism:export:{target}",
                    False,
                    type(exc).__name__,
                    "determinism",
                )
                summary[target] = {"error": type(exc).__name__}

        # Community dual inventory of repo names
        ca = base / "community-a"
        cb = base / "community-b"
        try:
            _export(monorepo, "community", ca, dry_run=False)
            _export(monorepo, "community", cb, dry_run=False)
            ra = sorted(p.name for p in ca.iterdir() if p.is_dir())
            rb = sorted(p.name for p in cb.iterdir() if p.is_dir())
            add_check(
                checks,
                defects,
                "determinism:community_repo_set",
                ra == rb,
                ",".join(ra),
                "determinism",
            )
            summary["community"] = {"repos": ra}
        except Exception as exc:  # noqa: BLE001
            add_check(
                checks,
                defects,
                "determinism:community_export",
                False,
                type(exc).__name__,
                "determinism",
            )

    return checks, defects, summary
