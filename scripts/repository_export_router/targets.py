"""Closed target vocabulary and registry (Slice 12.8)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExportTarget(str, Enum):
    COMMUNITY = "community"
    INFRASTRUCTURE = "infrastructure"


SUPPORTED_TARGETS = (ExportTarget.COMMUNITY, ExportTarget.INFRASTRUCTURE)

# Rejected aliases / non-targets (fail closed)
REJECTED_TARGET_TOKENS = frozenset(
    {
        "public",
        "private",
        "platform",
        "engine",
        "vscode",
        "cursor",
        "all",
        "both",
        "*",
        "community,infrastructure",
        "infrastructure,community",
    }
)


@dataclass(frozen=True, slots=True)
class TargetDescriptor:
    target: ExportTarget
    visibility: str
    manifest_schema: str
    destination_semantics: str
    handler: str


TARGET_REGISTRY: dict[ExportTarget, TargetDescriptor] = {
    ExportTarget.COMMUNITY: TargetDescriptor(
        target=ExportTarget.COMMUNITY,
        visibility="public_product_export",
        manifest_schema="codestrata.community_release:2",
        destination_semantics="export_staging_root_multiple_repositories",
        handler="community_adapter",
    ),
    ExportTarget.INFRASTRUCTURE: TargetDescriptor(
        target=ExportTarget.INFRASTRUCTURE,
        visibility="private",
        manifest_schema="infrastructure-repository-export-manifest:1.0.0",
        destination_semantics="single_repository_directory",
        handler="infrastructure_adapter",
    ),
}


def parse_target(raw: str | None) -> ExportTarget:
    from repository_export_router.errors import MissingTarget, UnknownTarget

    if raw is None or str(raw).strip() == "":
        raise MissingTarget("missing_target")
    value = str(raw).strip().lower()
    if "," in value or " " in value:
        raise UnknownTarget("unknown_target")
    if value in REJECTED_TARGET_TOKENS:
        raise UnknownTarget("unknown_target")
    try:
        return ExportTarget(value)
    except ValueError as exc:
        raise UnknownTarget("unknown_target") from exc
