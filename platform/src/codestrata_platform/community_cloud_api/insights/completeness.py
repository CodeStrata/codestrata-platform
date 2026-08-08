"""Completeness and limitation helpers."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights.models import Completeness, ReadDiagnostics
from codestrata_platform.community_cloud_api.insights.policy import BOUNDED_LIMITATIONS


def finalize_limitations(items: list[str]) -> tuple[str, ...]:
    out: list[str] = []
    for item in items:
        if item in BOUNDED_LIMITATIONS and item not in out:
            out.append(item)
    return tuple(sorted(out))


def resolve_completeness(
    *,
    diagnostics: ReadDiagnostics,
    missing_identity: bool,
    empty_source: bool = False,
    external_missing: bool = False,
    value_defined: bool = True,
) -> Completeness:
    if external_missing:
        return "unavailable"
    if empty_source and not value_defined:
        return "unavailable"
    if diagnostics.budget_reached:
        # Prefer partial when some objects were processed; unavailable if none usable.
        if diagnostics.objects_considered == 0:
            return "unavailable"
        return "partial"
    if diagnostics.malformed_objects or diagnostics.unsupported_schema_objects:
        return "partial"
    if missing_identity:
        return "partial"
    return "complete"
