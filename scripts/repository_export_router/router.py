"""Target router orchestration."""

from __future__ import annotations

from pathlib import Path

from repository_export_router.community_adapter import export_community_target
from repository_export_router.destination import require_destination
from repository_export_router.infrastructure_adapter import export_infrastructure_target
from repository_export_router.insights_adapter import export_insights_target
from repository_export_router.models import RouterResult
from repository_export_router.targets import ExportTarget, parse_target


def discover_source_root() -> Path:
    return Path(__file__).resolve().parents[2]


def export_repository(
    *,
    target: str | ExportTarget,
    destination: Path,
    dry_run: bool = False,
    source_root: Path | None = None,
) -> RouterResult:
    """Export exactly one target to the caller-provided destination."""

    parsed = target if isinstance(target, ExportTarget) else parse_target(target)
    require_destination(destination)
    root = source_root or discover_source_root()

    if parsed is ExportTarget.COMMUNITY:
        return export_community_target(
            destination=destination,
            dry_run=dry_run,
            source_root=root,
        )
    if parsed is ExportTarget.INFRASTRUCTURE:
        return export_infrastructure_target(
            destination=destination,
            dry_run=dry_run,
            source_root=root,
        )
    if parsed is ExportTarget.INSIGHTS:
        return export_insights_target(
            destination=destination,
            dry_run=dry_run,
            source_root=root,
        )
    from repository_export_router.errors import UnknownTarget

    raise UnknownTarget("unknown_target")


def print_human_summary(result: RouterResult) -> None:
    mode = "DRY-RUN" if result.dry_run else "EXPORT"
    print(f"[{mode}] target={result.target} status={result.status}")
    print(
        f"  visibility={result.visibility} "
        f"files={result.managed_file_count} "
        f"additions={result.additions} "
        f"modifications={result.modifications} "
        f"removals={result.removals} "
        f"conflicts={result.conflicts}"
    )
    print(
        f"  manifest={result.target_manifest_schema} "
        f"destination_semantics={result.destination_semantics} "
        f"dry_run={str(result.dry_run).lower()}"
    )
    if result.limitation_codes:
        print(f"  limitations={','.join(sorted(result.limitation_codes))}")
