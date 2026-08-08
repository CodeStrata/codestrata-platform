"""Bounded S3 reader consuming planner prefixes only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

from codestrata_platform.community_cloud_api.insights.errors import (
    QUERY_LIMIT_EXCEEDED,
    STORAGE_UNAVAILABLE,
    InsightsAggregationError,
)
from codestrata_platform.community_cloud_api.insights.models import ReadDiagnostics
from codestrata_platform.community_cloud_api.insights_query.models import QueryPlan
from codestrata_platform.community_cloud_api.insights_query.planner import reject_caller_prefix
from codestrata_platform.community_cloud_api.insights_storage.ports import InsightsS3ClientPort


@dataclass(frozen=True, slots=True)
class ObjectRecord:
    """Raw object bytes with size — never expose key outside storage layer."""

    size: int
    body: bytes
    # Key retained only inside reader for GetObject; stripped before domain handoff.
    _key: str = field(repr=False, compare=False)


@dataclass
class ReaderResult:
    objects: list[ObjectRecord]
    diagnostics: ReadDiagnostics


class BoundedS3Reader:
    """List+Get over planner prefixes with hard budget enforcement."""

    def __init__(self, *, bucket: str, client: InsightsS3ClientPort) -> None:
        self._bucket = bucket
        self._client = client

    def read_plan(self, plan: QueryPlan) -> ReaderResult:
        for prefix in plan.prefixes:
            self._assert_safe_prefix(prefix)

        diagnostics = ReadDiagnostics()
        records: list[ObjectRecord] = []
        budgets = plan.budgets

        try:
            for prefix in plan.prefixes:
                for key, size in self._list_prefix(prefix, plan, diagnostics):
                    if diagnostics.objects_considered >= budgets.max_objects_per_query:
                        diagnostics.budget_reached = True
                        raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "objects")
                    if size > budgets.max_single_object_bytes:
                        diagnostics.budget_reached = True
                        raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "single_object")
                    if diagnostics.bytes_read + size > budgets.max_bytes_per_query:
                        diagnostics.budget_reached = True
                        raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "bytes")
                    if diagnostics.get_requests >= budgets.max_get_requests_per_query:
                        diagnostics.budget_reached = True
                        raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "gets")

                    body = self._get_object(key, diagnostics)
                    actual = len(body)
                    if actual > budgets.max_single_object_bytes:
                        diagnostics.budget_reached = True
                        raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "single_object")
                    diagnostics.bytes_read += actual
                    diagnostics.objects_considered += 1
                    records.append(ObjectRecord(size=actual, body=body, _key=""))
        except InsightsAggregationError:
            raise
        except Exception:
            raise InsightsAggregationError(STORAGE_UNAVAILABLE, "read_failed") from None

        return ReaderResult(objects=records, diagnostics=diagnostics)

    def iter_plan(self, plan: QueryPlan) -> Iterator[tuple[ObjectRecord, ReadDiagnostics]]:
        """Generator-style processing to avoid holding all bodies when callers stream."""

        result = self.read_plan(plan)
        for obj in result.objects:
            yield obj, result.diagnostics

    def _assert_safe_prefix(self, prefix: str) -> None:
        if not prefix.startswith("raw/stream="):
            raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "unsafe_prefix")
        if "quarantine" in prefix or prefix == "raw/" or ".." in prefix or "*" in prefix:
            raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "unsafe_prefix")
    def _list_prefix(
        self, prefix: str, plan: QueryPlan, diagnostics: ReadDiagnostics
    ) -> Iterator[tuple[str, int]]:
        token: str | None = None
        pages_for_prefix = 0
        while True:
            if diagnostics.list_requests >= plan.budgets.max_list_requests_per_query:
                diagnostics.budget_reached = True
                raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "lists")
            if pages_for_prefix >= plan.budgets.max_pages_per_query:
                diagnostics.budget_reached = True
                raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "pages")
            kwargs: dict[str, Any] = {
                "Bucket": self._bucket,
                "Prefix": prefix,
                "MaxKeys": plan.budgets.max_keys_per_page,
            }
            if token:
                kwargs["ContinuationToken"] = token
            try:
                resp = self._client.list_objects_v2(**kwargs)
            except Exception:
                raise InsightsAggregationError(STORAGE_UNAVAILABLE, "list_failed") from None
            diagnostics.list_requests += 1
            diagnostics.pages_read += 1
            pages_for_prefix += 1
            for item in resp.get("Contents") or []:
                key = item.get("Key")
                if not isinstance(key, str):
                    continue
                size = int(item.get("Size") or 0)
                yield key, size
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
            if not token:
                break

    def _get_object(self, key: str, diagnostics: ReadDiagnostics) -> bytes:
        try:
            resp = self._client.get_object(Bucket=self._bucket, Key=key)
        except Exception:
            raise InsightsAggregationError(STORAGE_UNAVAILABLE, "get_failed") from None
        diagnostics.get_requests += 1
        body = resp.get("Body")
        if body is None:
            raise InsightsAggregationError(STORAGE_UNAVAILABLE, "empty_body")
        data = body.read() if hasattr(body, "read") else body
        if not isinstance(data, bytes):
            raise InsightsAggregationError(STORAGE_UNAVAILABLE, "bad_body")
        return data


def reject_arbitrary_prefix(prefix: str) -> None:
    """Public guard: never accept caller-supplied prefixes."""

    reject_caller_prefix(prefix)
