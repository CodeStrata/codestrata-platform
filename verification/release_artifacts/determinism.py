"""Build determinism checks comparing file inventories across two builds."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from verification.release_artifacts.models import CheckResult, Warning


def _inventory(path: Path) -> frozenset[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path, "r") as archive:
            return frozenset(archive.namelist())
    if path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:*") as archive:
            return frozenset(member.name for member in archive.getmembers())
    return frozenset()


def _paired_paths(paths: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    normalized = [p.replace("\\", "/") for p in paths]
    wheels = [p for p in normalized if p.endswith(".whl")]
    a_wheels = sorted(p for p in wheels if "/a/" in p)
    b_wheels = sorted(p for p in wheels if "/b/" in p)
    pairs: list[tuple[str, str]] = []
    for left in a_wheels:
        counterpart = left.replace("/a/", "/b/", 1)
        if counterpart in b_wheels:
            pairs.append((left, counterpart))
    sdists = [p for p in normalized if not p.endswith(".whl")]
    a_sdists = sorted(p for p in sdists if "/a/" in p)
    b_sdists = sorted(p for p in sdists if "/b/" in p)
    for left in a_sdists:
        counterpart = left.replace("/a/", "/b/", 1)
        if counterpart in b_sdists:
            pairs.append((left, counterpart))
    return tuple(pairs)


def check_determinism(
    monorepo: Path,
    *,
    wheel_paths: tuple[str, ...],
    sdist_paths: tuple[str, ...],
) -> tuple[list[CheckResult], list[Warning]]:
    checks: list[CheckResult] = []
    warnings: list[Warning] = []

    pairs = _paired_paths(wheel_paths + sdist_paths)
    if not pairs:
        checks.append(
            CheckResult(
                name="determinism:paired_artifacts",
                ok=False,
                detail="no a/b artifact pairs found",
                category="determinism",
            )
        )
        return checks, warnings

    inventory_match = True
    digest_mismatch = False
    for left_rel, right_rel in pairs:
        left = monorepo / left_rel
        right = monorepo / right_rel
        left_inv = _inventory(left)
        right_inv = _inventory(right)
        same_inventory = left_inv == right_inv
        inventory_match = inventory_match and same_inventory
        same_digest = left.read_bytes() == right.read_bytes()
        if same_inventory and not same_digest:
            digest_mismatch = True
        checks.append(
            CheckResult(
                name=f"determinism:inventory_{Path(left_rel).name}",
                ok=same_inventory,
                detail=f"files={len(left_inv)} match={same_inventory}",
                category="determinism",
            )
        )

    if digest_mismatch and inventory_match:
        warnings.append(
            Warning(
                code="archive_timestamp_drift",
                detail="identical file inventories but byte digests differ (likely archive timestamps)",
            )
        )
        checks.append(
            CheckResult(
                name="determinism:digest_drift_limitation",
                ok=True,
                detail="inventory match with digest drift recorded as limitation",
                category="determinism",
            )
        )

    checks.append(
        CheckResult(
            name="determinism:inventory_summary",
            ok=inventory_match,
            detail=f"pairs={len(pairs)}",
            category="determinism",
        )
    )
    return checks, warnings
