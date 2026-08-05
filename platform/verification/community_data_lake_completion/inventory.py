"""Package inventory for Community Data Lake completion verification (Slice 8.15)."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_completion.models import CheckResult

REPO = Path(__file__).resolve().parents[3]
PLATFORM_SRC = REPO / "platform" / "src" / "codestrata_platform"

_PACKAGE_TOKENS: tuple[str, ...] = (
    "platform/src/codestrata_platform/community_cloud_api/data_lake",
    "platform/src/codestrata_platform/community_cloud_api/data_lake/infrastructure",
    "platform/src/codestrata_platform/community_cloud_api/data_lake/streams",
    "infrastructure/modules/community-data-lake",
    "platform/verification/community_data_lake",
    "platform/verification/community_data_lake_completion",
)


def build_package_inventory() -> tuple[str, ...]:
    return tuple(sorted(_PACKAGE_TOKENS))


def check_package_inventory() -> list[CheckResult]:
    inventory = build_package_inventory()
    checks: list[CheckResult] = [
        CheckResult(
            name=f"inventory:token_exists:{token.replace('/', '_')}",
            ok=(REPO / token).exists(),
            detail=token,
            category="inventory",
        )
        for token in inventory
    ]
    checks.append(
        CheckResult(
            name="inventory:no_duplicate_runtime_outside_platform",
            ok=_no_duplicate_data_lake_outside_platform(),
            detail="scan clean",
            category="inventory",
        )
    )
    checks.append(
        CheckResult(
            name="inventory:sorted_stable",
            ok=list(inventory) == sorted(inventory),
            detail=f"count={len(inventory)}",
            category="inventory",
        )
    )
    return checks


def _no_duplicate_data_lake_outside_platform() -> bool:
    allowed_root = PLATFORM_SRC / "community_cloud_api" / "data_lake"
    offenders: list[str] = []
    for path in REPO.rglob("data_lake"):
        if not path.is_dir():
            continue
        if allowed_root in path.parents or path == allowed_root:
            continue
        rel = path.relative_to(REPO)
        rel_text = str(rel)
        if rel_text.startswith("platform/tests/"):
            continue
        if rel_text.startswith("platform/verification/"):
            continue
        if rel_text.startswith(".venv/") or "/.venv/" in rel_text:
            continue
        offenders.append(rel_text)
    return not offenders


__all__ = ["build_package_inventory", "check_package_inventory"]
