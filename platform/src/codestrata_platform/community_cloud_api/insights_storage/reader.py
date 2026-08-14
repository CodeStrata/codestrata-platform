"""Bounded S3 reader consuming planner prefixes only."""

from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date
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

# Month-prefix plans are small; keep a worker pool for multi-stream lifetime windows.
_LIST_WORKERS = 8
_LIST_FUTURE_TIMEOUT_SECONDS = 5.0
_LIST_TOTAL_TIMEOUT_SECONDS = 12.0
_GET_WORKERS = 16
_GET_FUTURE_TIMEOUT_SECONDS = 8.0
_GET_TOTAL_TIMEOUT_SECONDS = 20.0

_PARTITION_DAY_RE = re.compile(
    r"/year=(?P<year>\d{4})/month=(?P<month>\d{2})/day=(?P<day>\d{2})/"
)
_THREAD_LOCAL = threading.local()


def _partition_date_from_key(key: str) -> date | None:
    match = _PARTITION_DAY_RE.search(key)
    if match is None:
        return None
    try:
        return date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )
    except ValueError:
        return None


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
        budgets = plan.budgets
        window_start = date.fromisoformat(plan.start_date)
        window_end = date.fromisoformat(plan.end_date)

        try:
            listed = self._list_all_prefixes(plan, diagnostics)
            candidates: list[tuple[str, int]] = []
            estimated_bytes = 0
            for key, size in listed:
                part_day = _partition_date_from_key(key)
                if part_day is None or part_day < window_start or part_day > window_end:
                    continue
                if len(candidates) >= budgets.max_objects_per_query:
                    diagnostics.budget_reached = True
                    raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "objects")
                if size > budgets.max_single_object_bytes:
                    diagnostics.budget_reached = True
                    raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "single_object")
                if estimated_bytes + size > budgets.max_bytes_per_query:
                    diagnostics.budget_reached = True
                    raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "bytes")
                estimated_bytes += size
                candidates.append((key, size))

            if len(candidates) > budgets.max_get_requests_per_query:
                diagnostics.budget_reached = True
                raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "gets")

            records = self._get_objects_parallel(candidates, plan, diagnostics)
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

    def _client_for_worker(self) -> InsightsS3ClientPort:
        """Prefer a thread-local boto3 client; keep fakes shared."""

        client = self._client
        meta = getattr(client, "meta", None)
        if meta is None:
            return client
        cached = getattr(_THREAD_LOCAL, "s3_client", None)
        if cached is not None:
            return cached
        try:
            import boto3
            from botocore.config import Config

            region = getattr(meta, "region_name", None) or "us-west-2"
            created = boto3.client(
                "s3",
                region_name=region,
                config=Config(
                    connect_timeout=2,
                    read_timeout=5,
                    retries={"max_attempts": 2, "mode": "standard"},
                    max_pool_connections=32,
                ),
            )
            _THREAD_LOCAL.s3_client = created
            return created
        except Exception:
            return client

    def _get_objects_parallel(
        self,
        candidates: list[tuple[str, int]],
        plan: QueryPlan,
        diagnostics: ReadDiagnostics,
    ) -> list[ObjectRecord]:
        """Fetch object bodies; parallelize when many keys to stay under Lambda timeout."""

        if not candidates:
            return []

        budgets = plan.budgets
        if len(candidates) <= 4:
            out: list[ObjectRecord] = []
            for key, _size in candidates:
                body = self._get_object(key, diagnostics)
                actual = len(body)
                if actual > budgets.max_single_object_bytes:
                    diagnostics.budget_reached = True
                    raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "single_object")
                if diagnostics.bytes_read + actual > budgets.max_bytes_per_query:
                    diagnostics.budget_reached = True
                    raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "bytes")
                diagnostics.bytes_read += actual
                diagnostics.objects_considered += 1
                out.append(ObjectRecord(size=actual, body=body, _key=""))
            return out

        workers = min(_GET_WORKERS, len(candidates))
        bodies: dict[str, bytes] = {}

        def _fetch(key: str) -> tuple[str, bytes]:
            worker = self._client_for_worker()
            try:
                resp = worker.get_object(Bucket=self._bucket, Key=key)
            except Exception:
                raise InsightsAggregationError(STORAGE_UNAVAILABLE, "get_failed") from None
            body = resp.get("Body")
            if body is None:
                raise InsightsAggregationError(STORAGE_UNAVAILABLE, "empty_body")
            data = body.read() if hasattr(body, "read") else body
            if not isinstance(data, bytes):
                raise InsightsAggregationError(STORAGE_UNAVAILABLE, "bad_body")
            return key, data

        try:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_fetch, key) for key, _ in candidates]
                for fut in as_completed(futures, timeout=_GET_TOTAL_TIMEOUT_SECONDS):
                    key, data = fut.result(timeout=_GET_FUTURE_TIMEOUT_SECONDS)
                    bodies[key] = data
        except InsightsAggregationError:
            raise
        except Exception as exc:
            raise InsightsAggregationError(STORAGE_UNAVAILABLE, "get_parallel_failed") from exc

        diagnostics.get_requests += len(candidates)
        out_records: list[ObjectRecord] = []
        # Preserve deterministic key order for aggregation stability.
        for key, _size in sorted(candidates, key=lambda item: item[0]):
            body = bodies[key]
            actual = len(body)
            if actual > budgets.max_single_object_bytes:
                diagnostics.budget_reached = True
                raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "single_object")
            if diagnostics.bytes_read + actual > budgets.max_bytes_per_query:
                diagnostics.budget_reached = True
                raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "bytes")
            diagnostics.bytes_read += actual
            diagnostics.objects_considered += 1
            out_records.append(ObjectRecord(size=actual, body=body, _key=""))
        return out_records

    def _list_all_prefixes(
        self, plan: QueryPlan, diagnostics: ReadDiagnostics
    ) -> list[tuple[str, int]]:
        """List every planner prefix; parallelize larger multi-month plans."""

        prefixes = plan.prefixes
        if not prefixes:
            return []

        if len(prefixes) <= 4:
            out: list[tuple[str, int]] = []
            for prefix in prefixes:
                for key, size in self._list_prefix(prefix, plan, diagnostics, self._client):
                    out.append((key, size))
            return out

        workers = min(_LIST_WORKERS, len(prefixes))
        collected: list[tuple[str, int]] = []
        list_requests = 0
        pages_read = 0

        def _collect(prefix: str) -> tuple[list[tuple[str, int]], int, int]:
            local_diag = ReadDiagnostics()
            worker_client = self._client_for_worker()
            items = list(self._list_prefix(prefix, plan, local_diag, worker_client))
            return items, local_diag.list_requests, local_diag.pages_read

        try:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_collect, prefix) for prefix in prefixes]
                for fut in as_completed(futures, timeout=_LIST_TOTAL_TIMEOUT_SECONDS):
                    items, lists, pages = fut.result(timeout=_LIST_FUTURE_TIMEOUT_SECONDS)
                    list_requests += lists
                    pages_read += pages
                    if list_requests >= plan.budgets.max_list_requests_per_query:
                        diagnostics.list_requests = list_requests
                        diagnostics.pages_read = pages_read
                        diagnostics.budget_reached = True
                        raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "lists")
                    collected.extend(items)
        except InsightsAggregationError:
            raise
        except Exception as exc:
            diagnostics.list_requests = list_requests
            diagnostics.pages_read = pages_read
            raise InsightsAggregationError(STORAGE_UNAVAILABLE, "list_parallel_failed") from exc

        diagnostics.list_requests += list_requests
        diagnostics.pages_read += pages_read
        collected.sort(key=lambda item: item[0])
        return collected

    def _list_prefix(
        self,
        prefix: str,
        plan: QueryPlan,
        diagnostics: ReadDiagnostics,
        client: InsightsS3ClientPort,
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
                resp = client.list_objects_v2(**kwargs)
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
