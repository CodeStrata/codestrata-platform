"""Fake S3 client with ListObjectsV2 + GetObject for Insights tests."""

from __future__ import annotations

from typing import Any


class FakeInsightsS3Error(Exception):
    def __init__(self, code: str, operation: str = "GetObject") -> None:
        super().__init__(operation)
        self.response = {"Error": {"Code": code, "Message": "synthetic"}}
        self.operation_name = operation


class FakeInsightsS3Client:
    """In-memory object store keyed by S3 key (no network)."""

    def __init__(self) -> None:
        import threading

        self.objects: dict[str, bytes] = {}
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.fail_list: bool = False
        self.fail_get: bool = False
        self._lock = threading.Lock()

    def put_bytes(self, key: str, body: bytes) -> None:
        self.objects[key] = body

    def list_objects_v2(self, **kwargs: Any) -> dict[str, Any]:
        with self._lock:
            self.calls.append(("list_objects_v2", dict(kwargs)))
        if self.fail_list:
            raise FakeInsightsS3Error("ServiceUnavailable", "ListObjectsV2")
        prefix = kwargs.get("Prefix") or ""
        if prefix.startswith("quarantine/") or prefix == "raw/":
            raise AssertionError("unsafe prefix listed")
        token = kwargs.get("ContinuationToken")
        max_keys = int(kwargs.get("MaxKeys") or 1000)
        keys = sorted(k for k in self.objects if k.startswith(prefix))
        start = int(token) if token else 0
        page = keys[start : start + max_keys]
        next_start = start + len(page)
        contents = [
            {"Key": k, "Size": len(self.objects[k])} for k in page
        ]
        out: dict[str, Any] = {"Contents": contents, "KeyCount": len(contents)}
        if next_start < len(keys):
            out["IsTruncated"] = True
            out["NextContinuationToken"] = str(next_start)
        else:
            out["IsTruncated"] = False
        return out

    def get_object(self, **kwargs: Any) -> dict[str, Any]:
        with self._lock:
            self.calls.append(("get_object", dict(kwargs)))
        if self.fail_get:
            raise FakeInsightsS3Error("ServiceUnavailable", "GetObject")
        key = kwargs["Key"]
        if key not in self.objects:
            raise FakeInsightsS3Error("NoSuchKey", "GetObject")
        body = self.objects[key]

        class _Body:
            def __init__(self, data: bytes) -> None:
                self._data = data

            def read(self) -> bytes:
                return self._data

        return {"Body": _Body(body), "ContentLength": len(body)}
