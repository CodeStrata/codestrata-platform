"""Translate RetrievalFilters / RetrievalScope into VectorFilter predicates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from aimf.domain.knowledge.retrieval import (
    RetrievalDiagnostic,
    RetrievalFilters,
    RetrievalScope,
)
from aimf.domain.knowledge.vector import VectorFilter, VectorSearchResult

# Metadata keys projected onto VectorRecord.metadata by the indexer.
_LIST_FILTER_KEYS: dict[str, str] = {
    "source_types": "source_type",
    "intelligence_packs": "intelligence_pack",
    "severities": "severity",
    "file_paths": "file_path",
    "symbol_names": "symbol_name",
    "finding_ids": "finding_id",
    "rule_ids": "rule_id",
}


class FilterValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_diagnostic(self) -> RetrievalDiagnostic:
        return RetrievalDiagnostic(code=self.code, message=self.message, severity="error")


def validate_retrieval_filters(filters: RetrievalFilters) -> None:
    """Reject blank or structurally invalid filter values."""

    for attr, meta_key in _LIST_FILTER_KEYS.items():
        values = getattr(filters, attr)
        for item in values:
            if not str(item).strip():
                raise FilterValidationError(
                    "filter_validation_failure",
                    f"blank value in filter {attr} ({meta_key})",
                )
    for key in filters.equals:
        if not key.strip():
            raise FilterValidationError(
                "filter_validation_failure",
                "equals keys must not be blank",
            )


def build_base_vector_filter(scope: RetrievalScope) -> VectorFilter:
    """Tenant/repository isolation; optional scan when supplied."""

    return VectorFilter(
        tenant_id=scope.tenant_id,
        repository_id=scope.repository_id,
        scan_id=scope.scan_id,
    )


def build_scope_equals(scope: RetrievalScope) -> dict[str, Any]:
    """Optional branch/commit equality filters from scope."""

    equals: dict[str, Any] = {}
    if scope.branch is not None:
        equals["branch"] = scope.branch
    if scope.commit_sha is not None:
        equals["commit_sha"] = scope.commit_sha
    return equals


def build_vector_filter(
    scope: RetrievalScope,
    filters: RetrievalFilters,
) -> VectorFilter:
    """Build a VectorFilter for store.search.

    Multi-value list filters (OR within a facet) are applied post-search via
    ``post_filter_hits`` because VectorFilter.equals is equality-only.
    Single-value list filters and equals are pushed into VectorFilter.
    """

    validate_retrieval_filters(filters)
    equals = dict(build_scope_equals(scope))
    equals.update(filters.equals)

    # Push singleton list filters into equals for store-side filtering.
    for attr, meta_key in _LIST_FILTER_KEYS.items():
        values: tuple[str, ...] = getattr(filters, attr)
        if len(values) == 1:
            equals[meta_key] = values[0]

    return VectorFilter(
        tenant_id=scope.tenant_id,
        repository_id=scope.repository_id,
        scan_id=scope.scan_id,
        equals=equals,
    )


def post_filter_hits(
    hits: Sequence[VectorSearchResult],
    *,
    scope: RetrievalScope,
    filters: RetrievalFilters,
) -> tuple[list[VectorSearchResult], int]:
    """Apply multi-value OR filters and re-check isolation; return (kept, excluded)."""

    kept: list[VectorSearchResult] = []
    excluded = 0
    multi: dict[str, set[str]] = {}
    for attr, meta_key in _LIST_FILTER_KEYS.items():
        values: tuple[str, ...] = getattr(filters, attr)
        if len(values) > 1:
            multi[meta_key] = set(values)

    for hit in hits:
        meta = hit.record.metadata
        if meta.get("tenant_id") != scope.tenant_id:
            excluded += 1
            continue
        if meta.get("repository_id") != scope.repository_id:
            excluded += 1
            continue
        if scope.scan_id is not None and meta.get("scan_id") != scope.scan_id:
            excluded += 1
            continue
        if scope.branch is not None and meta.get("branch") != scope.branch:
            excluded += 1
            continue
        if scope.commit_sha is not None and meta.get("commit_sha") != scope.commit_sha:
            excluded += 1
            continue
        drop = False
        for meta_key, allowed in multi.items():
            value = meta.get(meta_key)
            if value is None or str(value) not in allowed:
                drop = True
                break
        if drop:
            excluded += 1
            continue
        for key, expected in filters.equals.items():
            if meta.get(key) != expected:
                drop = True
                break
        if drop:
            excluded += 1
            continue
        kept.append(hit)
    return kept, excluded
